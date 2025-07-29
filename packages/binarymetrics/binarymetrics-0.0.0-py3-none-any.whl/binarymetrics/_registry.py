import functools
import inspect
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol
from warnings import warn

from safecheck import typecheck

from ._types import TFloat, TInt


class ConfusionMetric(Protocol):
    def __call__(
        self,
        tp: TInt["t"],
        fp: TInt["t"],
        tn: TInt["t"],
        fn: TInt["t"],
    ) -> TFloat["t"]:
        ...


@dataclass(frozen=True)
class Metric:
    name: str
    aliases: set[str]
    func: ConfusionMetric


class MetricRegistry:
    """Registry for confusion-matrix metrics.

    The registry keeps track of metrics by their primary name and any aliases
    they may have, enforcing uniqueness of all keys.
    """

    def __init__(self):
        self._metrics: dict[str, Metric] = {}
        self._alias_to_name: dict[str, str] = {}
        self.raise_on_existing: bool = True
        self.warn_on_existing: bool = True
        self._aliases_cache: dict[str, Metric] | None = None

    def add(
        self,
        name: str,
        aliases: Iterable[str] | None,
        func: ConfusionMetric,
    ) -> None:
        """Register a new metric under ``name``.

        Parameters
        ----------
        name : str
            Primary name of the metric.
        aliases : Iterable[str] or None
            Optional alternative names.
        func : Callable
            Function implementing the metric.
        """
        aliases = set(aliases or [])
        # check primary + aliases for conflicts
        for key in (name, *aliases):
            if key in self._metrics or key in self._alias_to_name:
                msg = f"'{key}' conflicts with existing metric"
                if self.raise_on_existing:
                    raise ValueError(msg)
                if self.warn_on_existing:
                    warn(msg + ", overriding")

                # if warning only, remove old entries so we can re-add
                self._remove_nolock(key)

        # store the Metric
        metric = Metric(name=name, aliases=aliases, func=func)
        self._metrics[name] = metric
        for alias in aliases:
            self._alias_to_name[alias] = name

        # invalidate alias cache
        self._aliases_cache = None

    def get(self, key: str) -> Metric:
        """Return the metric registered under ``key``.

        Parameters
        ----------
        key : str
            Primary name or alias.

        Returns
        -------
        Metric
            The registered metric.
        """
        if key in self._metrics:
            return self._metrics[key]
        if key in self._alias_to_name:
            primary = self._alias_to_name[key]
            return self._metrics[primary]
        raise KeyError(f"No metric registered under {key!r}")

    def __getitem__(self, key: str) -> Metric:
        return self.get(key)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key in self._metrics or key in self._alias_to_name

    def items(self) -> Iterator[tuple[str, Metric]]:
        """Iterate over primary metric names and their objects."""
        return iter(self._metrics.items())

    def clear(self) -> None:
        """Remove all metrics and aliases from the registry."""
        self._metrics.clear()
        self._alias_to_name.clear()
        self._aliases_cache = None

    def remove(self, key: str) -> None:
        """Delete a metric by either its primary name or an alias."""
        if key in self._metrics:
            # remove all its aliases too
            for alias in self._metrics[key].aliases:
                self._alias_to_name.pop(alias, None)
            self._metrics.pop(key)
        elif key in self._alias_to_name:
            primary = self._alias_to_name.pop(key)
            # if alias, leave other aliases intact
            self._metrics[primary].aliases.discard(key)
        else:
            raise KeyError(f"No metric registered under {key!r}")
        self._aliases_cache = None

    def update(self, other: dict[str, Metric]) -> None:
        """Bulk-add existing metrics.

        Parameters
        ----------
        other : dict[str, Metric]
            Mapping of metric names to :class:`Metric` objects. The metrics are
            inserted using :meth:`add` so normal conflict checks apply.
        """
        for name, metric in other.items():
            self.add(name, metric.aliases, metric.func)

    @property
    def aliases(self) -> dict[str, Metric]:
        """Lazily computed mapping of aliases to metrics."""
        if self._aliases_cache is None:
            self._aliases_cache = {
                alias: self._metrics[primary]
                for alias, primary in self._alias_to_name.items()
            }
        return self._aliases_cache

    def _remove_nolock(self, key: str) -> None:
        """Delete ``key`` from the registry without any checks."""
        if key in self._metrics:
            for a in self._metrics[key].aliases:
                self._alias_to_name.pop(a, None)
            self._metrics.pop(key, None)
        self._alias_to_name.pop(key, None)


# instantiate the global registry
metric_registry = MetricRegistry()


# decorator to register metrics
def register_metric(
    fn: ConfusionMetric | None = None,
    *,
    name: str | None = None,
    aliases: Iterable[str] | None = None
) -> ConfusionMetric | Callable[[ConfusionMetric], ConfusionMetric]:
    """
    Decorator to register a new confusion-matrix metric.
    Usage:
      @register_metric
      def recall(tp, fp, tn, fn): ...

      @register_metric(name="acc", aliases=["accuracy"])
      def _accuracy(tp, fp, tn, fn): ...
    """
    def _ensure_signature(func: ConfusionMetric):
        sig = inspect.signature(func)
        if list(sig.parameters) != ["tp", "fp", "tn", "fn"]:
            raise TypeError(f"{func.__name__!r} must take (tp, fp, tn, fn)")
        return func

    def decorator(func: ConfusionMetric):
        func = _ensure_signature(func)
        func = functools.wraps(func)(typecheck(func))
        metric_registry.add(
            name=name or func.__name__,
            aliases=aliases or (),
            func=func
        )
        return func

    # support both @register_metric and @register_metric(...)
    return decorator if fn is None else decorator(fn)
