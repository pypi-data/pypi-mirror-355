"""
Types
=====

Courtesy's custom typing framework. This is an implementation detail.

"""

import logging
from abc import ABC
from dataclasses import dataclass
from enum import Flag, auto
from os import PathLike

from courtesy.errors import NamespaceError


logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CourtesyProjectType(Flag):
    """
    An enumeration of the languages that Courtesy currenetly supports

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
class CourtesyProject:
    name: str
    project_type: CourtesyProjectType
    is_persistent: bool
    root_path: PathLike
    dependencies: dict[str, list]


@dataclass
class CourtesyPythonProject(CourtesyProject):
    project_type = CourtesyProjectType.PYTHON


@dataclass
class CourtesyCppProject(CourtesyProject):
    project_Type = CourtesyProjectType.CPP


@dataclass
class CourtesyHaskellProject(CourtesyProject):
    project_type = CourtesyProjectType.HASKELL


@dataclass
class CourtesyJavaScriptProject(CourtesyProject):
    project_type = CourtesyProjectType.JAVASCRIPT


@dataclass
class CourtesyRProject(CourtesyProject):
    project_type = CourtesyProjectType.R


@dataclass
class CourtesyRustProject(CourtesyProject):
    project_type = CourtesyProjectType.RUST


@dataclass
class CourtesySwiftProject(CourtesyProject):
    project_type = CourtesyProjectType.SWIFT


class CourtesyNamespace(ABC):
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

