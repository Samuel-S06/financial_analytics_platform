"""Tests for the simulation module."""

import pytest

from app.analysis import parser
from app.analysis.simulation import SimulationRequest, simulate


def test_feasible_simulation(sample_csv: bytes) -> None:
    """
    Goal: $300 over 12 months = $25/month.
    Cuttable: Dining (290/3 = 96.67/mo) + Transport (105/3 = 35/mo) = 131.67/mo.
    25 << 131.67, so feasible.
    """
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=300.0,
        months=12,
        cut_categories=["Dining", "Transport"],
    )
    result = simulate(df, req)

    assert result["feasible"] is True
    assert result["required_monthly_savings"] == 25.0
    assert len(result["cuts"]) == 2
    assert "warning" not in result


def test_proportional_distribution(sample_csv: bytes) -> None:
    """
    Cut should be split proportionally to current spend. Dining is ~73% of
    cuttable, Transport ~27%, so cuts should be in those proportions.
    """
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=120.0,  # 10/mo over 12 months
        months=12,
        cut_categories=["Dining", "Transport"],
    )
    result = simulate(df, req)

    cuts_by_cat = {c["category"]: c for c in result["cuts"]}
    # Dining cut should be ~3x Transport cut (since Dining is ~3x Transport spend)
    assert cuts_by_cat["Dining"]["reduction_amount"] > cuts_by_cat["Transport"]["reduction_amount"]
    # Sum of cuts should equal required monthly savings
    total_cut = sum(c["reduction_amount"] for c in result["cuts"])
    assert abs(total_cut - 10.0) < 0.05  # allow for rounding


def test_infeasible_goal(sample_csv: bytes) -> None:
    """
    Goal: $5000 over 1 month = $5000/month required cuts. Total cuttable is
    far less - should flag as infeasible.
    """
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=5000.0,
        months=1,
        cut_categories=["Dining"],
    )
    result = simulate(df, req)

    assert result["feasible"] is False
    assert "warning" in result
    assert "Goal not achievable" in result["warning"]


def test_unknown_categories_ignored_silently(sample_csv: bytes) -> None:
    """Categories not in the data should be ignored, not error out."""
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=120.0,
        months=12,
        cut_categories=["Dining", "NonexistentCategory"],
    )
    result = simulate(df, req)

    # Only Dining should appear in cuts
    assert len(result["cuts"]) == 1
    assert result["cuts"][0]["category"] == "Dining"


def test_all_unknown_categories_returns_warning(sample_csv: bytes) -> None:
    """If NONE of the requested categories exist, return a clear warning."""
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=120.0,
        months=12,
        cut_categories=["Foo", "Bar"],
    )
    result = simulate(df, req)

    assert result["feasible"] is False
    assert result["cuts"] == []
    assert "category names match" in result["warning"]


def test_validates_inputs(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)

    with pytest.raises(ValueError, match="months"):
        simulate(df, SimulationRequest(goal_amount=100, months=0, cut_categories=["A"]))

    with pytest.raises(ValueError, match="goal_amount"):
        simulate(df, SimulationRequest(goal_amount=-10, months=12, cut_categories=["A"]))

    with pytest.raises(ValueError, match="cut category"):
        simulate(df, SimulationRequest(goal_amount=100, months=12, cut_categories=[]))