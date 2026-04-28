"""Tests for analytics."""

from app.analysis import analytics, parser


def test_summary_totals(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    summary = analytics.summary(df)
    assert summary["total_spend"] == 920.0
    assert summary["months_covered"] == 3


def test_by_category_sorted(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    rows = analytics.by_category(df)
    assert [r["category"] for r in rows] == ["Groceries", "Dining", "Transport"]


def test_monthly_spending(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    months = analytics.monthly_spending(df)
    assert len(months) == 3
    assert months[0]["month"] == "2024-01"
