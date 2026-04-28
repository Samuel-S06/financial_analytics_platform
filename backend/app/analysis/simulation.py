"""Savings goal simulation."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class SimulationRequest:
    goal_amount: float
    months: int
    cut_categories: list[str]


def simulate(df: pd.DataFrame, req: SimulationRequest) -> dict:
    if req.months <= 0:
        raise ValueError("months must be positive")
    if req.goal_amount < 0:
        raise ValueError("goal_amount cannot be negative")
    if not req.cut_categories:
        raise ValueError("at least one cut category must be provided")

    months_in_data = max(df["date"].dt.to_period("M").nunique(), 1)
    monthly_avg = (df.groupby("category")["amount"].sum() / months_in_data).to_dict()

    cuttable = {cat: monthly_avg[cat] for cat in req.cut_categories if cat in monthly_avg}

    if not cuttable:
        return {
            "feasible": False,
            "required_monthly_savings": req.goal_amount / req.months,
            "cuts": [],
                        "warning": (
                "None of the requested cut categories appear in the "
                "transaction data. Check the category names match."
            ),
        }

    required_monthly = req.goal_amount / req.months
    total_cuttable_monthly = sum(cuttable.values())
    feasible = required_monthly <= total_cuttable_monthly

    cuts = []
    for category, current in cuttable.items():
        share = current / total_cuttable_monthly if total_cuttable_monthly > 0 else 0
        reduction = min(required_monthly * share, current)
        recommended = current - reduction

        cuts.append({
            "category": category,
            "current_monthly": round(current, 2),
            "recommended_monthly": round(recommended, 2),
            "reduction_amount": round(reduction, 2),
            "reduction_percentage": round((reduction / current * 100) if current > 0 else 0, 1),
        })

    cuts.sort(key=lambda c: c["reduction_amount"], reverse=True)

    result = {
        "feasible": feasible,
        "required_monthly_savings": round(required_monthly, 2),
        "total_cuttable_monthly": round(total_cuttable_monthly, 2),
        "cuts": cuts,
    }

    if not feasible:
        shortfall = required_monthly - total_cuttable_monthly
        result["warning"] = (
            f"Goal not achievable: need ${required_monthly:.2f}/mo in cuts "
            f"but selected categories only total ${total_cuttable_monthly:.2f}/mo. "
            f"Short by ${shortfall:.2f}/mo."
        )

    return result
