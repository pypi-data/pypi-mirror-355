"""
Types
=====

Gnarly's custom typing framework. This is an implementation detail.

"""

import logging
from abc import ABC
from dataclasses import dataclass
from enum import Flag, auto
from os import PathLike

from gnarly.errors import NamespaceError


logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GnarlyProjectType(Flag):
    """
    An enumeration of the languages that Gnarly currenetly supports

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


# ─── Interfaces ────────────────────────────────────────────────────────── ✦ ─
@dataclass
class GnarlyProject:
    name: str
    project_type: GnarlyProjectType
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


@dataclass
class GnarlyJavaScriptProject(GnarlyProject):
    project_type = GnarlyProjectType.JAVASCRIPT


@dataclass
class GnarlyRProject(GnarlyProject):
    project_type = GnarlyProjectType.R


@dataclass
class GnarlyRustProject(GnarlyProject):
    project_type = GnarlyProjectType.RUST


@dataclass
class GnarlySwiftProject(GnarlyProject):
    project_type = GnarlyProjectType.SWIFT


class GnarlyNamespace(ABC):
    """
    Base class for non-instantiable types that serve to encapsulate.

    Subclasses of this ABC provide no constructors. Instead, attempts
    to instantiate raise `NamespaceError`.
    """
    context_key: str

    def __new__(cls) -> NamespaceError:
        logger.error("`Project` is not intended for direct instantiation.")
        raise NamespaceError(
            f"`{cls.__name__}` is a namespace, which means that it "
            "has no constructors. Instead, you should call one of its "
            "provided, static factory methods."
        )

