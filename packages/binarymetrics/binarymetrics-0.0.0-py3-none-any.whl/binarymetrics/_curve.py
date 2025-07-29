import importlib
from collections.abc import Callable, Iterable
from dataclasses import dataclass, fields
from functools import cached_property
from typing import Any, NamedTuple

import torch
from scipy.spatial import ConvexHull

from ._types import TFloat

__all__ = [
    "CurveMixin",
    "CurveT",
    "PlotMixin",
    "binary_curve",
]

CurveT = tuple[TFloat["t"], TFloat["t"], TFloat["t"]]

# Check if matplotlib is available
MATPLOTLIB_AVAILABLE = importlib.util.find_spec("matplotlib") is not None


def binary_curve(_cls: type | None = None, *, mixins: Iterable[type]):
    """Decorate a dataclass to represent a binary curve.

    Parameters
    ----------
    _cls : type, optional
        Class being decorated when used without parentheses.
    mixins : Iterable[type]
        Additional mixins to include alongside :class:`CurveMixin`.

    Returns
    -------
    type
        The decorated dataclass.
    """
    def wrap(cls: type) -> type:
        # copy over the class dict (minus dataclass-internal bits)
        namespace = dict(cls.__dict__)
        namespace.pop("__dict__", None)
        namespace.pop("__weakref__", None)

        # make a fresh subclass with the required CurveMixin
        NewCls = type(cls.__name__, (CurveMixin, *mixins), namespace)

        # finally apply your frozen/eq=False/repr=False dataclass
        return dataclass(frozen=True, eq=False, repr=False)(NewCls)

    # allow usage both with and without params
    if _cls is None:
        return wrap
    else:
        return wrap(_cls)


class PlotMixin:
    def plot(self, *, use_hull: bool = True):
        """Plot the curve using ``matplotlib``.

        Parameters
        ----------
        use_hull : bool, default=True
            Plot the convex hull instead of the raw curve.
        """
        import matplotlib.pyplot as plt
        _, x, y = self.hull if use_hull else self.value
        plt.plot(x, y)
        plt.show()


if not MATPLOTLIB_AVAILABLE:
    # Create empty mixin if matplotlib is unavailable
    PlotMixin = type("PlotMixin", (), {})


@dataclass(frozen=True, eq=False, repr=False)
class CurveMixin:
    threshold: TFloat["t"]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        annotations = cls.__annotations__

        # look at the annotated fields of the sub-dataclass to ensure there are exactly two (a valid curve)
        if (n_annotations := len(annotations)) != 2:
            msg = (
                f"@binary_curve-decorated class {cls.__name__!r} must define exactly two fields representing the "
                f"x and y coordinates of the binary curve, got {n_annotations}: {list(annotations)}"
            )
            raise TypeError(msg)

    @property
    def value(self) -> CurveT:
        """Return the curve as ``(t, x, y)`` tensors."""
        f = [getattr(self, field.name) for field in fields(self)]
        return self.tuple(*f)

    @cached_property
    def hull(self):
        """Convex hull of the curve."""
        t, x, y = self.value
        hull = ConvexHull(torch.stack([x, y], dim=1), incremental=False)
        vs = hull.vertices
        vs.sort()
        return self.tuple(t[vs], x[vs], y[vs])

    @cached_property
    def tuple(self):
        """Return a ``NamedTuple`` representation of the curve."""
        cls = self.__class__
        tuple_name = f"{cls.__name__}Tuple"
        annotations = {"threshold": TFloat["t"]} | {k: v for k, v in cls.__annotations__.items()}
        t = NamedTuple(tuple_name, **annotations)
        t.__repr__ = _create_repr(tuple_name, annotations.keys(), lambda instance: len(instance[0]))
        return t

    def __repr__(self):
        """Return ``repr(self)`` using the dynamic ``NamedTuple``."""
        names = [field.name for field in fields(self)]

        def size(self):
            return len(getattr(self, names[0]))

        return _create_repr(self.__class__.__name__, names, size)(self)


def _create_repr(
    name: str,
    keys: Iterable[str],
    size: Callable[[Any], int]
) -> Callable[[Any], str]:
    """Create a compact ``repr`` function for NamedTuple instances."""
    return lambda self: f"{name}({', '.join(keys)}) of size {size(self)}"
