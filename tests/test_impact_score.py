import pandas as pd

from analysis.impact_score import _safe_min_max_normalize


def test_safe_min_max_normalize_returns_zeroes_for_constant_series():
    series = pd.Series([5, 5, 5], dtype="float64")

    normalized = _safe_min_max_normalize(series)

    assert normalized.tolist() == [0.0, 0.0, 0.0]


def test_safe_min_max_normalize_scales_variable_series():
    series = pd.Series([10, 20, 30], dtype="float64")

    normalized = _safe_min_max_normalize(series)

    assert normalized.round(4).tolist() == [0.0, 0.5, 1.0]
