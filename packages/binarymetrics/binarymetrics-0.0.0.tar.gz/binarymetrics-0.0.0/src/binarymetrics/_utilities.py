from typing import Any, Literal, overload

import numpy as np
import torch
from scipy.ndimage import gaussian_filter
from torch import Tensor


def fast_sort(values: Tensor) -> Tensor:
    """Return ``values`` sorted in descending order.

    Parameters
    ----------
    values : torch.Tensor
        1D tensor to sort.

    Returns
    -------
    tuple[torch.Tensor, torch.Tensor]
        The sorted tensor and the indices used to obtain it.
    """
    torch_idx = fast_argsort(values)
    return values.take(torch_idx), torch_idx


def fast_argsort(values: Tensor) -> Tensor:
    """Return the indices that would sort ``values`` in descending order.

    Parameters
    ----------
    values : torch.Tensor
        1D tensor to sort.

    Returns
    -------
    torch.Tensor
        Indices that sort ``values`` in descending order.
    """
    np_idx = np.argsort(-values.ravel().numpy(force=True))
    return torch.from_numpy(np_idx)


@overload
def auc_compute(
    x: Tensor,
    y: Tensor,
    limit: float = 1.0,
    *,
    descending: bool = False,
    reorder: bool = False,
    check: bool = True,
    return_curve: Literal[True] = False,
) -> tuple[Tensor, Tensor, Tensor]: ...


@overload
def auc_compute(
    x: Tensor,
    y: Tensor,
    limit: float = 1.0,
    *,
    descending: bool = False,
    reorder: bool = False,
    check: bool = True,
    return_curve: Literal[False] = False,
) -> Tensor: ...


def auc_compute(
    x: Tensor,
    y: Tensor,
    limit: float = 1.0,
    *,
    descending: bool = False,
    reorder: bool = False,
    check: bool = True,
    return_curve: bool = False,
) -> Tensor | tuple[Tensor, Tensor, Tensor]:
    """Compute the area under a curve using the trapezoidal rule.

    Parameters
    ----------
    x, y : torch.Tensor
        Tensors of equal length describing the curve. ``x`` must be sorted in
        ascending order unless ``reorder`` is ``True``.
    limit : float, default=1.0
        Only the portion of ``x`` up to ``limit`` is considered.
    descending : bool, default=False
        Whether ``x`` is sorted in descending order.
    reorder : bool, default=False
        If ``True``, ``x`` and ``y`` will be sorted according to ``x``.
    check : bool, default=True
        Validate that ``x`` is monotonic if ``reorder`` is ``False``.
    return_curve : bool, default=False
        If ``True``, also return the processed ``x`` and ``y`` tensors.

    Returns
    -------
    torch.Tensor or tuple[torch.Tensor, torch.Tensor, torch.Tensor]
        The computed area or ``(area, x, y)`` if ``return_curve`` is ``True``.

    Examples
    --------
    >>> import torch
    >>> x = torch.tensor([1, 2, 3, 4])
    >>> y = torch.tensor([1, 2, 3, 4])
    >>> auc_compute(x, y)
    tensor(7.5000)
    """
    assert limit > 0, "The `limit` parameter must be > 0."

    with torch.no_grad():
        if reorder:
            x, x_idx = torch.sort(x, descending=descending)
            y = y[x_idx]

        if check and not reorder:
            dx = torch.diff(x)
            if descending:
                assert (dx <= 0).all(), "The `x` tensor is not descending."
            else:
                assert (dx >= 0).all(), "The `x` tensor is not ascending."

        if limit != 1.0:
            # searchsorted expects a monotonically increasing tensor
            x_sorted = x.flip() if descending else x
            limit_idx = torch.searchsorted(x_sorted, limit)
            limit_idx = len(x) - limit_idx if descending else limit_idx
            x, y = x[:limit_idx], y[:limit_idx]

        direction = -1.0 if descending else 1.0
        auc_score = torch.trapz(y, x) * direction
        auc_score = auc_score / limit
        return (auc_score, x, y) if return_curve else auc_score


def generate_random_data(
    batch_size: int = 8,
    height: int = 32,
    width: int = 32,
    num_objects: int = 2,
    noise_level: float = 0.25,
    return_numpy: bool = False,
    seed: Any = None,  # dynamically validated in ``default_rng
) -> tuple[Tensor, Tensor] | tuple[np.ndarray, np.ndarray]:
    """Generate random binary masks and probabilistic predictions.

    Parameters
    ----------
    batch_size : int, default=8
        Number of samples to generate.
    height : int, default=32
        Height of the generated masks.
    width : int, default=32
        Width of the generated masks.
    num_objects : int, default=2
        Number of objects to draw in each mask.
    noise_level : float, default=0.25
        Standard deviation of the added Gaussian noise.
    return_numpy : bool, default=False
        If ``True``, return ``numpy`` arrays instead of tensors.
    seed : Any, optional
        Seed for ``numpy.random.default_rng``.

    Returns
    -------
    tuple[Tensor, Tensor] or tuple[numpy.ndarray, numpy.ndarray]
        Prediction probabilities and corresponding binary masks.
    """
    rng = np.random.default_rng(seed)
    preds = np.zeros((batch_size, height, width), dtype=np.float32)
    masks = np.zeros((batch_size, height, width), dtype=np.int32)

    for i in range(batch_size):
        # Generate random object positions
        object_centers = rng.integers(0, (height, width), size=(num_objects, 2))

        # Create binary mask with objects
        for y, x in object_centers:
            masks[i, max(0, y - 2) : min(height, y + 3), max(0, x - 2) : min(width, x + 3)] = 1

        # Generate probabilistic prediction by blurring and adding noise
        preds[i] = gaussian_filter(masks[i].astype(np.float32), sigma=2)
        preds[i] += noise_level * rng.standard_normal((height, width))
        preds[i] = np.clip(preds[i], 0, 1)  # Keep probabilities in [0,1]

    if return_numpy:
        return preds, masks

    return torch.from_numpy(preds), torch.from_numpy(masks)
