from typing import TypeVar
from koil.composition import Composition
from .rath import AlpakaRath

T = TypeVar("T")


class Alpaka(Composition):
    rath: AlpakaRath
