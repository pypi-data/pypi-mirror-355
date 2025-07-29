import typing

import cleo.io.io
import cleo.io.outputs.output
from poetry.core.pyproject.toml import PyProjectTOML
from poetry.core.constraints.version import Version
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.dependency_group import DependencyGroup


def _validate_pinning_strategy(strategy):
    if not strategy in ["mixed", "semver", "exact"]:
        raise ValueError(f"Invalid version pinning strategy: {strategy}")


class PathDependencyRewriter:
    """
    Exposes core functionality for gathering a pyproject.toml's path dependencies,
    determining if they are Poetry projects, and if so, extracting the corresponding
    dependency version and replacing the path dependency with its versioned equivalent.
    """

    def __init__(self, version_pinning_strategy):
        _validate_pinning_strategy(version_pinning_strategy)
        self._version_pinning_strategy = version_pinning_strategy

    def update_dependency_group(
        self,
        io: cleo.io.io.IO,
        pyproject: PyProjectTOML,
        dependency_group: DependencyGroup,
    ) -> None:
        """
        Replaces all path dependencies to Poetry projects defined within the given dependency
        group with their versioned dependency equivalents.  The specific strategy for pinning
        the version of the Poetry project path dependency (which is extracted via its
        pyproject.toml) is determined via the configured _version_pinning_strategy.

        :param io: instance of Cleo IO that may be used for logging diagnostic output during
        plugin execution
        :param pyproject: encapsulates the pyproject.toml of the current project for which
        path dependencies will be rewritten
        :param dependency_group: specifies the dependency group from which to pin path
        dependencies, this will usually be "main"
        :return: none
        """
        io.write_line(
            "Updating dependency constraints...",
            verbosity=cleo.io.outputs.output.Verbosity.DEBUG,
        )

        for dependency in dependency_group.dependencies:
            if not isinstance(
                dependency,
                DirectoryDependency,
            ):
                continue

            pinned = self._pin_dependency(pyproject, dependency)

            if dependency is pinned:
                continue

            io.write_line(
                f"  • Pinning {pinned.name} ({pinned.constraint}')",
                verbosity=cleo.io.outputs.output.Verbosity.DEBUG,
            )

            dependency_group.remove_dependency(dependency.name)
            dependency_group.add_dependency(pinned)

    def _extract_project_info(
        self, pyproject_toml: PyProjectTOML
    ) -> typing.Tuple[str, str]:
        """
        Extracts the project name and version from the provided pyproject.toml file.
        Supports both [tool.poetry] and [project] formats as valid sources of metadata.

        :param pyproject_toml: parsed representation of the pyproject.toml file
        :return: a tuple containing the project name and version as strings
        """
        tool_poetry_config = pyproject_toml.poetry_config
        project_config = pyproject_toml.data.get("project", {})

        name = tool_poetry_config.get("name") or project_config.get("name")
        version = tool_poetry_config.get("version") or project_config.get("version")

        return typing.cast(str, name), typing.cast(str, version)

    def _pin_dependency(
        self, pyproject: PyProjectTOML, dependency: DirectoryDependency
    ) -> Dependency:
        """
        Helper method that determines if the given path dependency is for a valid Poetry
        project and if so, creates a new Dependency that has its version pinned based on
        the configured _version_pinning_strategy (and existing path related metadata
        stripped).  If the given path dependency does *not* align with a Poetry project
        (i.e. is a path to an existing wheel), the originally provided path dependency
        will be returned.

        :param pyproject: encapsulates the pyproject.toml of the current project for which
        the given path dependency will be rewritten
        :param dependency: path dependency for which to create a new versioned dependency
        without any path information
        :return: appropriately versioning package dependency equivalent of the given
        path dependency.
        """
        pyproject_file = pyproject.path.parent / dependency.path / "pyproject.toml"

        if not pyproject_file.exists():
            return dependency

        pyproject_toml = PyProjectTOML(pyproject_file)

        if not pyproject_toml.is_poetry_project():
            return dependency

        name, version = self._extract_project_info(pyproject_toml)
        pinned_version = version
        if self._version_pinning_strategy == "semver":
            pinned_version = f"^{version}"
        elif self._version_pinning_strategy == "mixed":
            parsed_version = Version.parse(version)
            if parsed_version.is_unstable():
                # For any dev or pre-releases, use the next patch version as the upper-bound
                # in order to provide better compatibility with pip-based version ordering
                next_patch_version = parsed_version.replace(
                    dev=None, pre=None
                ).next_patch()
                pinned_version = f">={version},<{next_patch_version}"

        new_dependency = Dependency(
            name,
            pinned_version,
            groups=dependency.groups,
        )

        # handle cases where dependency is part of an extra.
        if dependency.in_extras:
            new_dependency._optional = dependency._optional
            new_dependency._in_extras = dependency._in_extras

        return new_dependency
