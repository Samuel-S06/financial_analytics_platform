"""
Savings goal simulation.

Given a user's transaction history, a savings target, a timeframe, and a list
of categories to cut from, compute per-category recommended new monthly
budgets. The cut is distributed proportionally to each category's current
share of the cuttable total (so big categories get bigger cuts in absolute
terms, but everyone takes the same percentage hit).

Out of scope (kept simple deliberately): inflation, income changes,
non-linear spending patterns, category interactions. This is a demo, not a
real planning tool.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class SimulationRequest:
    """Inputs to the simulation."""
    goal_amount: float           # total savings target in dollars
    months: int                  # over how many months to spread the savings
    cut_categories: list[str]    # which categories the user is willing to cut


def simulate(df: pd.DataFrame, req: SimulationRequest) -> dict:
    """
    Compute per-category budget recommendations.

    Returns a dict with:
      - feasible: bool (can the goal be met without zeroing out a category?)
      - required_monthly_savings: float
      - cuts: list of {category, current_monthly, recommended_monthly,
                       reduction_amount, reduction_percentage}
      - warning: optional message if infeasible or overly aggressive
    """
    # Validate inputs early with clear error messages.
    if req.months <= 0:
        raise ValueError("months must be positive")
    if req.goal_amount < 0:
        raise ValueError("goal_amount cannot be negative")
    if not req.cut_categories:
        raise ValueError("at least one cut category must be provided")

    # How many months of data we have. Used to compute the "current monthly
    # spend" baseline per category - we want averages, not totals.
    months_in_data = max(df["date"].dt.to_period("M").nunique(), 1)

    # Average monthly spend per category, computed from the full dataset.
    # We index by category for easy lookup below.
    monthly_avg = (
        df.groupby("category")["amount"].sum() / months_in_data
    ).to_dict()

    # Filter to just the categories the user is willing to cut. Silently
    # ignore categories they listed that don't exist in their data - the
    # alternative (erroring) is annoying when a user has slightly different
    # category spellings between their CSV and their input.
    cuttable = {
        cat: monthly_avg[cat]
        for cat in req.cut_categories
        if cat in monthly_avg
    }

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

    # Feasibility: can we hit the savings target without driving any single
    # category below zero? If required cut > total cuttable, the answer is no.
    feasible = required_monthly <= total_cuttable_monthly

    cuts = []
    for category, current in cuttable.items():
        # Each category contributes proportionally to its share of the
        # cuttable pool. A category that's 50% of cuttable spending takes
        # 50% of the required cut.
        share = current / total_cuttable_monthly if total_cuttable_monthly > 0 else 0
        reduction = required_monthly * share

        # Cap reduction at the current spend - we never recommend a negative
        # budget. When infeasible, the cap activates here.
        reduction = min(reduction, current)
        recommended = current - reduction

        cuts.append({
            "category": category,
            "current_monthly": round(current, 2),
            "recommended_monthly": round(recommended, 2),
            "reduction_amount": round(reduction, 2),
            "reduction_percentage": round(
                (reduction / current * 100) if current > 0 else 0, 1
            ),
        })

    # Sort by reduction amount descending - biggest cuts first, which is
    # what the user cares about most.
    cuts.sort(key=lambda c: c["reduction_amount"], reverse=True)

    result = {
        "feasible": feasible,
        "required_monthly_savings": round(required_monthly, 2),
        "total_cuttable_monthly": round(total_cuttable_monthly, 2),
        "cuts": cuts,
    }

    # Surface a clear warning if the goal can't actually be met under the
    # given constraints. The frontend should display this prominently.
    if not feasible:
        shortfall = required_monthly - total_cuttable_monthly
        result["warning"] = (
            f"Goal not achievable: need ${required_monthly:.2f}/mo in cuts "
            f"but selected categories only total ${total_cuttable_monthly:.2f}/mo. "
            f"Short by ${shortfall:.2f}/mo. Consider a longer timeframe, "
            f"smaller goal, or cuts from more categories."
        )

    return result