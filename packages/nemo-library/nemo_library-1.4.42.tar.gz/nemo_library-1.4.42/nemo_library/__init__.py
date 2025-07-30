import typing

if typing.TYPE_CHECKING:
    from .core import NemoLibrary
else:
    try:
        from .core import NemoLibrary
    except ImportError:
        pass