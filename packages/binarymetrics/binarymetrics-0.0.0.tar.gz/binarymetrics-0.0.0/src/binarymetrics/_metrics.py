from collections import OrderedDict
from collections.abc import Iterable

import torch

from ._registry import metric_registry, register_metric
from ._types import TFloat, TInt


def compute_metrics(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
    names: Iterable[str],
    values_only: bool = False,
) -> OrderedDict[str, TFloat["t"]] | tuple[TFloat["t"], ...]:
    """
    Compute multiple confusion-matrix metrics at once.

    Parameters
    ----------
    tp, fp, tn, fn : TInt["t"]
        True-positive, false-positive, true-negative, and false-negative counts,
        each a tensor of shape (T,).
    *names : str
        One or more metric names or aliases to compute. If empty, computes _all_
        registered metrics.
    values_only : bool, optional (default=False)
        If True, return only a tuple of metric _values_ in the order requested;
        if False, return an OrderedDict mapping each metric _name_ to its value.

    Returns
    -------
    OrderedDict[str, TFloat["t"]]
        If `values_only=False`, an ordered mapping from each requested metric
        name to its computed tensor.
    tuple[TFloat["t"], ...]
        If `values_only=True`, a tuple of computed tensors, in the same order
        as the metric names.

    Examples
    --------
    >>> # return a dict of three metrics
    >>> compute_metrics(tp, fp, tn, fn, 'accuracy', 'f1_score')
    OrderedDict([('accuracy', tensor(...)), ('f1_score', tensor(...))])
    >>> # return just the values
    >>> compute_metrics(tp, fp, tn, fn, 'accuracy', 'f1_score', values_only=True)
    (tensor(...), tensor(...))
    """
    results: OrderedDict[str, TFloat[t]] = OrderedDict()
    for name in names:
        metric = metric_registry[name]  # supports aliases
        results[name] = metric.func(tp, fp, tn, fn)

    return tuple(results.values()) if values_only else results

@register_metric
def positive(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TInt["t"]:
    """Actual positives: TP + FN."""
    return tp + fn

@register_metric
def negative(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TInt["t"]:
    """Actual negatives: TN + FP."""
    return tn + fp

@register_metric
def total(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TInt["t"]:
    """Total samples: TP + FP + TN + FN."""
    return tp + fp + tn + fn

@register_metric
def prevalence(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Prevalence = (TP + FN) / Total."""
    return (tp + fn) / total(tp, fp, tn, fn)

@register_metric(aliases=["acc"])
def accuracy(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Accuracy = (TP + TN) / Total."""
    return (tp + tn) / total(tp, fp, tn, fn)

@register_metric(aliases=["ba"])
def balanced_accuracy(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Balanced accuracy = (TPR + TNR) / 2."""
    return (true_positive_rate(tp, fp, tn, fn) +
            true_negative_rate(tp, fp, tn, fn)) * 0.5

@register_metric(aliases=["tpr", "recall", "sensitivity"])
def true_positive_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """TPR / Recall = TP / (TP + FN)."""
    return tp / (tp + fn)

@register_metric(aliases=["fpr", "fall_out"])
def false_positive_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """FPR = FP / (FP + TN)."""
    return fp / (fp + tn)

@register_metric(aliases=["tnr", "specificity", "selectivity"])
def true_negative_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """TNR / Specificity = TN / (TN + FP)."""
    return tn / (tn + fp)

@register_metric(aliases=["fnr", "miss_rate"])
def false_negative_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """FNR = FN / (TP + FN)."""
    return fn / (tp + fn)

@register_metric(aliases=["fdr"])
def false_discovery_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """FDR = FP / (TP + FP)."""
    return fp / (tp + fp)

@register_metric
def f1_score(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """F1 = 2·TP / (2·TP + FP + FN)."""
    return 2 * tp / (2 * tp + fp + fn)

@register_metric(aliases=["for"])
def false_omission_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """FOR = FN / (TN + FN)."""
    return fn / (tn + fn)

@register_metric(aliases=["npv"])
def negative_predictive_value(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """NPV = TN / (TN + FN)."""
    return tn / (tn + fn)

@register_metric(aliases=["ppv", "precision"])
def positive_predictive_value(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """PPV / Precision = TP / (TP + FP)."""
    return tp / (tp + fp)

@register_metric(aliases=["plr"])
def positive_likelihood_ratio(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """PLR = TPR / FPR."""
    return true_positive_rate(tp, fp, tn, fn) / false_positive_rate(tp, fp, tn, fn)

@register_metric(aliases=["nlr"])
def negative_likelihood_ratio(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """NLR = FNR / TNR."""
    return false_negative_rate(tp, fp, tn, fn) / true_negative_rate(tp, fp, tn, fn)

@register_metric(aliases=["threat_score", "critical_success_index"])
def jaccard_index(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Jaccard / CSI = TP / (TP + FP + FN)."""
    return tp / (tp + fp + fn)

@register_metric(aliases=["phi", "matthews_correlation_coefficient", "mcc"])
def phi_coefficient(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Matthews correlation coefficient."""
    num = tp * tn - fp * fn
    den = torch.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return num / den

@register_metric(aliases=["fmi"])
def fowlkes_mallows_index(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Fowlkes-Mallows index = sqrt(PPV · TPR)."""
    return torch.sqrt(
        positive_predictive_value(tp, fp, tn, fn) *
        true_positive_rate(tp, fp, tn, fn)
    )

@register_metric(aliases=["mk"])
def markedness(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Markedness = PPV + NPV - 1."""
    return (
        positive_predictive_value(tp, fp, tn, fn) +
        negative_predictive_value(tp, fp, tn, fn) - 1
    )

@register_metric
def informedness(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Informedness = TPR + TNR - 1."""
    return (
        true_positive_rate(tp, fp, tn, fn) +
        true_negative_rate(tp, fp, tn, fn) - 1
    )

@register_metric(aliases=["dor"])
def diagnostic_odds_ratio(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """DOR = PLR / NLR."""
    return (
        positive_likelihood_ratio(tp, fp, tn, fn) /
        negative_likelihood_ratio(tp, fp, tn, fn)
    )

@register_metric(aliases=["pt"])
def prevalence_threshold(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Prevalence threshold = (√(TPR·FPR) - FPR) / (TPR - FPR)."""
    tpr = true_positive_rate(tp, fp, tn, fn)
    fpr = false_positive_rate(tp, fp, tn, fn)
    return (torch.sqrt(tpr * fpr) - fpr) / (tpr - fpr)

@register_metric(aliases=["gmean"])
def geometric_mean(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """G-mean = √(TPR · TNR)."""
    return torch.sqrt(
        true_positive_rate(tp, fp, tn, fn) *
        true_negative_rate(tp, fp, tn, fn)
    )

@register_metric(aliases=["er"])
def error_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Error rate = (FP + FN) / Total."""
    return (fp + fn) / total(tp, fp, tn, fn)

@register_metric(aliases=["ber"])
def balanced_error_rate(
    tp: TInt["t"],
    fp: TInt["t"],
    tn: TInt["t"],
    fn: TInt["t"],
) -> TFloat["t"]:
    """Balanced Error Rate = (FNR + FPR) / 2."""
    return (false_negative_rate(tp, fp, tn, fn) +
            false_positive_rate(tp, fp, tn, fn)) * 0.5
