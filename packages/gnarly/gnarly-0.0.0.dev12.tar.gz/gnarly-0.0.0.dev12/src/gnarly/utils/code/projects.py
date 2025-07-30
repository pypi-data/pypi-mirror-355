"""
Projects
========

This module defines and implements various facilities useful for
project management.

"""
import logging
from os import PathLike
from pathlib import Path

from ...constants import GNARLY_PROJECT_ROOT_PATH
# from ...errors import NamespaceError
from ...types import (
    GnarlyCppProject,
    GnarlyHaskellProject,
    GnarlyJavaScriptProject,
    GnarlyNamespace,
    GnarlyProject,
    GnarlyProjectType,
    GnarlyPythonProject,
    GnarlyRProject,
    GnarlyRustProject,
    GnarlySwiftProject
)

logger: logging.Logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logging.BASIC_FORMAT)


class Project(GnarlyNamespace):
    """
    A namespace for Gnarly Code's project management utility suite.

    This is a Gnarly implementation detail. It is not intended for direct
    instantiation. Attempts to instantiate this class will raise a
    ``NamespaceError``.
    """


    class Python(GnarlyNamespace):
        """
        A namespace for Gnarly's Python project management utilities.

        Use the static functions defined in the ``Project.Python`` namespace
        to manage your Python project's code base.

        Examples
        --------
        Basic usage:

        >>> from pprint import pprint
        >>> from gnarly import Project
        >>> 
        >>> mgr = Project.Python()
        >>>
        >>> pr: GnarlyPythonProject = mgr.create("my_python_project")
        >>> pprint(pr)
        GnarlyPythonProject(name='my_python_project',
                            project_type=<GnarlyProjectType.PYTHON: 8>,
                            logger=<RootLogger root (INFO)>,
                            is_persistent=True,
                            root_path=PosixPath('/Users/u/gnarly/gnarly_project'),
                            dependencies={'dev': [], 'optional': [], 'required': []})
        
        """
        def __init__(
            self,
            context_key: str = "python_project_namespace"
        ) -> None:
            self._context_key = context_key


        @property
        def context_key(self) -> str:
            return self._context_key

        @context_key.setter
        def context_key(self, value: str) -> None:
            self._context_key = value

        @context_key.deleter
        def context_key(self) -> None:
            del self._context_key


        @staticmethod
        def create(
            name: str = "gnarly_python_project",
            project_type = GnarlyProjectType.PYTHON,
            is_persistent: bool = True,
            dependencies: dict[str, list[str]] = {
                "dev": [],
                "optional": [],
                "required": []
            }
        ) -> GnarlyPythonProject:
            """
            Create a Python project.

            Rather than instantiating ``GnarlyPythonProject`` directly, you
            call this static method on the ``Project.Python`` namespace.

            Parameters
            ----------
            name : str
                The Python project's name.
            project_type : GnarlyProjectType
                The project's type, as characterized by its target
                language configuration.
            is_persistent : bool
                The project's persistence state. Defaults to ``True``.
            root_path : PathLike
                The project's root path.
            dependencies : dict[str, list[str]]
                A dictionary that represents the project's dependencies.

            Returns
            -------
            A new instance of ``GnarlyPythonProject``.
            
            """
            root_path = GNARLY_PROJECT_ROOT_PATH / name
            root_path.mkdir(parents=True, exist_ok=True)

            root_path_filenames: list[str] = [
                "README.md",
                "LICENSE.txt",
                "pyproject.toml"
            ]
            for p in root_path_filenames:
                Path(root_path, p).touch(exist_ok=True)
                logger.info(f"Created {p}")

            core_package_dir: Path = root_path / f"src/{name}"
            core_package_dir.mkdir(parents=True, exist_ok=True)
            

            return Project.create(
                name=name,
                project_type=project_type,
                is_persistent=is_persistent,
                root_path=root_path,
                dependencies=dependencies
            )


    @staticmethod
    def create(
        name: str,
        project_type: GnarlyProjectType,
        is_persistent: bool = True,
        root_path: PathLike = GNARLY_PROJECT_ROOT_PATH,
        dependencies: dict[str, list] = {
            "dev": [],
            "optional": [],
            "required": []
        }
    ) -> "GnarlyProject":
        match project_type:
            case project_type.CPP:
                return GnarlyCppProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.HASKELL:
                return GnarlyHaskellProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.JAVASCRIPT:
                return GnarlyJavaScriptProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.PYTHON:
                return GnarlyPythonProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.R:
                return GnarlyRProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.RUST:
                return GnarlyRustProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.SWIFT:
                return GnarlySwiftProject(
                    name=name,
                    project_type=project_type,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )

