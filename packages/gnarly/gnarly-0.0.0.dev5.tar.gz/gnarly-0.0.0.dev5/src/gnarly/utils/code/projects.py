"""
Projects
========

This module defines and implements various facilities useful for
project management.

"""
from dataclasses import dataclass
from enum import Enum, auto
import logging
from os import PathLike

from ...constants import GNARLY_PROJECT_ROOT_PATH
from ...errors import NamespaceError

logger: logging.Logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format=logging.BASIC_FORMAT)

class GnarlyProjectType(Enum):
    """
    An enumeration of currently supported languages.

    Reference members of this class directly whenever you want to specify
    a language constraint. Avoid hard-coding comparisons to their `values`,
    since their integer data types are semantically insignificant.
    """
    CPP: int = auto()
    HASKELL: int = auto()
    JAVASCRIPT: int = auto()
    PYTHON: int = auto()
    R: int = auto()
    RUST: int = auto()
    SWIFT: int = auto()


class Project:
    """
    A namespace for Gnarly Code's project management utility suite.

    This is a Gnarly implementation detail. It is not intended for direct
    instantiation. Attempts to instantiate this class will raise a
    `NamespaceError`.
    """
    def __new__(cls) -> None:
        logger.error("`Project` is not intended for direct instantiation.")
        raise NamespaceError(
            f"Canot instantiate namespace class {cls.__name__}"
        )

    # ─── Utility Groups ──────────────────────────────────────────────────────
    class Python:
        """
        A namespace for Gnarly's Python project management utilities.

        Use the static functions defined in the `Project.Python` namespace to
        manage your Python project's code base.

        Examples
        --------
        Basic usage:

        >>> from gnarly.utils.code import Project
        >>> p = Project.Python                      # Alias for convenience.
        >>> p.create("my_project")
        GnarlyPythonProject(
            name="my_project",
            project_type=GnarlyProjectType.PYTHON,
            logger=None,
            is_persistent=True,
            root_path=Path(
                "/users/gnarly-user/gnarly/projects/python/my_project/"
            ),
            dependencies={"dev": [], "optional": [], "required": []}
        )

        With custom options:

        >>> from gnarly.utils.code import Project
        >>> p = Project.Python
        >>> p.create(
        ...     name="My Project",
        ...     project_type=
        ... )
        GnarlyPythonProject(
            name="my_project",
            project_type=GnarlyProjectType.PYTHON,            
            logger=None,
            is_persistent=True,
            root_path=Path(
                "/users/gnarly-user/gnarly/projects/python/my_project/"
            ),
            dependencies={"dev": [], "optional": [], "required": []}
        )
        """
        def create(
            cls,
            logger: logging.Logger = logging.getLogger(__name__),
            name: str = __package__,
            project_type = GnarlyProjectType.PYTHON,
            is_persistent: bool = True,
            root_path: PathLike = GNARLY_PROJECT_ROOT_PATH / f"{__package__}/",
            dependencies: dict[str, list] = {
                "dev": [],
                "optional": [],
                "required": []
            }
        ) -> "GnarlyPythonProject":
            return Project.create(
                name=__package__,
                project_type=GnarlyProjectType.PYTHON,
                logger=(
                    logging.getLogger(__class__)
                    .basicConfig(
                        level=logging.ERROR,
                        format=logging.BASIC_FORMAT
                    )
                ),
                is_persistent=is_persistent,
                root_path=root_path,
                dependencies=dependencies
            )


    @staticmethod
    def create(
        name: str,
        project_type: GnarlyProjectType,
        logger: logging.Logger = logger,
        is_persistent: bool = True,
        root_path: PathLike = GNARLY_PROJECT_ROOT_PATH,
        dependencies: dict[str, list] = {
            "dev": [],
            "optional": [],
            "required": []
        }
    ) -> "GnarlyProject":
        match project_type:
            case project_type.HASKELL:
                return GnarlyHaskellProject(
                    name=name,
                    project_type=project_type,
                    logger=logger,
                    is_persistent=is_persistent,
                    root_path=root_path,
                    dependencies=dependencies
                )
            case project_type.PYTHON:
                return GnarlyPythonProject
            case project_type.R:
                return GnarlyRProject
            case project_type.RUST:
                return GnarlyRustProject
            case project_type.SWIFT:
                return GnarlySwiftProject


@dataclass
class GnarlyProject:
    name: str
    project_type: GnarlyProjectType
    logger: logging.Logger
    is_persistent: bool
    root_path: PathLike
    dependencies: dict[str, list]


@dataclass
class GnarlyPythonProject(GnarlyProject):
    project_type = GnarlyProjectType.PYTHON


@dataclass
class GnarlyCppProject(GnarlyProject):
    project_Type = GnarlyProjectType.CPP


@dataclass
class GnarlyHaskellProject(GnarlyProject):
    project_type = GnarlyProjectType.HASKELL
    pass


@dataclass
class GnarlyJavaScriptProject(GnarlyProject):
    project_type = GnarlyProjectType.JAVASCRIPT
    pass


@dataclass
class GnarlyRProject(GnarlyProject):
    project_type = GnarlyProjectType.R


@dataclass
class GnarlyRustProject(GnarlyProject):
    project_type = GnarlyProjectType.RUST
    pass


@dataclass
class GnarlySwiftProject(GnarlyProject):
    project_type = GnarlyProjectType.SWIFT
    pass

