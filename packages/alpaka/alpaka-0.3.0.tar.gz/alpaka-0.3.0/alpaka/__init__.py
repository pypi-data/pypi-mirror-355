from .alpaka import Alpaka

try:
    from .arkitekt import AlpakaService
    from .rekuest import structure_reg
except ImportError:
    pass


__all__ = [
    "Alpaka",
    "AlpakaService",
    "structure_reg",
]
