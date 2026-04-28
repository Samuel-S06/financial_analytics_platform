"""Tests for simulation."""

import pytest

from app.analysis import parser
from app.analysis.simulation import SimulationRequest, simulate


def test_feasible_simulation(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=300.0, months=12, cut_categories=["Dining", "Transport"],
    )
    result = simulate(df, req)
    assert result["feasible"] is True
    assert result["required_monthly_savings"] == 25.0


def test_infeasible_goal(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=5000.0, months=1, cut_categories=["Dining"],
    )
    result = simulate(df, req)
    assert result["feasible"] is False
    assert "warning" in result


def test_unknown_categories_ignored(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    req = SimulationRequest(
        goal_amount=120.0, months=12,
        cut_categories=["Dining", "NonexistentCategory"],
    )
    result = simulate(df, req)
    assert len(result["cuts"]) == 1


def test_validates_inputs(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    with pytest.raises(ValueError):
        simulate(df, SimulationRequest(
            goal_amount=100, months=0, cut_categories=["A"],
        ))
