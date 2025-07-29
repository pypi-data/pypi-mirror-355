from ._compute import compute_confusion
from ._curve import CurveMixin, PlotMixin, binary_curve
from ._metrics import compute_metrics
from ._utilities import auc_compute, generate_random_data


def get_version() -> str:
    """Return the installed package version.

    Returns
    -------
    str
        Version string or ``"no-version-found-in-package-metadata"`` if the
        package metadata is missing.
    """
    from importlib import metadata

    try:
        return metadata.version(__name__)
    except metadata.PackageNotFoundError:  # pragma: no cover
        return "no-version-found-in-package-metadata"


__version__ = get_version()
