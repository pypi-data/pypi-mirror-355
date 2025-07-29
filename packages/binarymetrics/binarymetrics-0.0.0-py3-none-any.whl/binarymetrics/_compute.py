import torch

from ._types import TFloat, TInt
from ._utilities import fast_sort

__all__ = [
    "compute_confusion"
]

def compute_confusion(
    preds: TFloat["n *other"],
    target: TInt["n *other"],
) -> tuple[TInt["n_flat"], TInt["n_flat"], TInt["n_flat"], TInt["n_flat"], TFloat["n_flat"]]:
    """Compute cumulative confusion-matrix counts.

    Parameters
    ----------
    preds : TFloat["n *other"]
        Prediction scores.
    target : TInt["n *other"]
        Corresponding binary labels.

    Returns
    -------
    tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]
        ``(tp, fp, tn, fn, sorted_scores)`` where each tensor has length
        ``n_flat``.

    Notes
    -----
    ``preds`` are sorted in descending order and cumulative sums are used to
    derive the confusion counts without constructing negative masks.

    Examples
    --------
    >>> preds = torch.tensor([0.2, 0.8, 0.5, 0.3, 0.9])
    >>> target = torch.tensor([0, 1, 1, 0, 1])
    >>> tp, fp, tn, fn, scores = compute_confusion(preds, target)
    >>> print(scores)
    tensor([0.9000, 0.8000, 0.5000, 0.3000, 0.2000])
    """
    # Flatten predictions and get sort indices in descending order
    flat_preds, sort_idx = fast_sort(preds)

    # Gather the ground-truth labels according to sorted prediction indices.
    # gt_positive[i] is 1 if the i-th highest-scored element is a positive example.
    gt_positive = (target.ravel() == 1).take(sort_idx)

    # Count total positives and negatives
    num_positives = gt_positive.sum()
    num_elements = gt_positive.numel()
    num_negatives = num_elements - num_positives

    # Convert boolean tensor to integer (0/1) so we can do a cumulative sum in-place.
    true_positive = gt_positive.to(torch.long)

    # In-place cumulative sum: true_positive[i] = count of positives among
    # the top (i+1) sorted predictions.
    torch.cumsum(true_positive, dim=0, out=true_positive)

    # Build a tensor [1, 2, ..., num_elements] on the appropriate device & dtype
    # Then subtract true_positive in-place to get false_positive counts.
    false_positive = torch.arange(
        1,
        num_elements + 1,
        device=target.device,
        dtype=true_positive.dtype,
    ).sub_(true_positive)

    # False negatives at each threshold = total positives - cumulative true positives
    false_negative = num_positives - true_positive

    # True negatives at each threshold = total negatives - cumulative false positives
    true_negative = num_negatives - false_positive

    return true_positive, false_positive, true_negative, false_negative, flat_preds
