"""
Spending analytics.

Operates on the normalized DataFrame produced by the parser. Returns plain
Python dicts/lists that can be JSON-serialized by FastAPI without needing a
custom encoder for pandas/numpy types.
"""

import pandas as pd


def by_category(df: pd.DataFrame) -> list[dict]:
    """
    Total spend per category, sorted descending.

    Returns a list of {category, total, transaction_count} dicts so the
    frontend can render a bar chart or pie chart directly. Sorted so the
    biggest categories appear first - useful for "where is my money going"
    visualizations.
    """
    grouped = df.groupby("category").agg(
        total=("amount", "sum"),
        transaction_count=("amount", "count"),
    )
    grouped = grouped.sort_values("total", ascending=False).reset_index()

    return [
        {
            "category": row["category"],
            # Round to cents - JSON floats with 12 decimal places look weird.
            "total": round(float(row["total"]), 2),
            "transaction_count": int(row["transaction_count"]),
        }
        for _, row in grouped.iterrows()
    ]


def monthly_spending(df: pd.DataFrame) -> list[dict]:
    """
    Total spend per month across all categories.

    Returns a list of {month, total} dicts sorted chronologically. "month" is
    a YYYY-MM string for easy display and stable sorting in JSON.
    """
    # Group by year-month period rather than calendar date so spending in
    # different days of the same month aggregates together.
    by_month = df.groupby(df["date"].dt.to_period("M")).agg(
        total=("amount", "sum"),
    )
    by_month = by_month.reset_index()

    return [
        {
            "month": str(row["date"]),  # PeriodIndex -> "2024-01"
            "total": round(float(row["total"]), 2),
        }
        for _, row in by_month.iterrows()
    ]


def summary(df: pd.DataFrame) -> dict:
    """
    Top-level summary stats. The headline numbers for a dashboard view.
    """
    total = float(df["amount"].sum())
    months_covered = df["date"].dt.to_period("M").nunique()

    return {
        "total_spend": round(total, 2),
        "transaction_count": len(df),
        # Avoid divide-by-zero if all transactions are in the same month.
        "average_monthly_spend": round(total / max(months_covered, 1), 2),
        "months_covered": int(months_covered),
        "category_count": int(df["category"].nunique()),
        "date_range": {
            "start": df["date"].min().date().isoformat(),
            "end": df["date"].max().date().isoformat(),
        },
    }


def full_analysis(df: pd.DataFrame) -> dict:
    """
    Run all analyses at once. This is what gets returned from the /results
    endpoint after a job completes.
    """
    return {
        "summary": summary(df),
        "by_category": by_category(df),
        "monthly_spending": monthly_spending(df),
        "rows_kept": int(df.attrs.get("rows_kept", len(df))),
        "rows_dropped": int(df.attrs.get("rows_dropped", 0)),
    }