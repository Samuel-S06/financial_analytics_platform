"""Tests for the analytics module."""

from app.analysis import analytics, parser


def test_summary_totals(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    summary = analytics.summary(df)

    assert summary["total_spend"] == 920.0
    assert summary["transaction_count"] == 9
    assert summary["months_covered"] == 3
    # 920 / 3 = 306.666... rounded to 2dp
    assert summary["average_monthly_spend"] == 306.67
    assert summary["category_count"] == 3


def test_by_category_sorted_descending(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    rows = analytics.by_category(df)

    # Groceries is biggest (525), then Dining (290), then Transport (105)
    assert [r["category"] for r in rows] == ["Groceries", "Dining", "Transport"]
    assert rows[0]["total"] == 525.0
    assert rows[1]["total"] == 290.0
    assert rows[2]["total"] == 105.0


def test_by_category_includes_counts(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    rows = analytics.by_category(df)
    # Each category has exactly 3 transactions in the fixture
    for r in rows:
        assert r["transaction_count"] == 3


def test_monthly_spending_chronological(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    months = analytics.monthly_spending(df)

    # 3 months in fixture, in calendar order
    assert [m["month"] for m in months] == ["2024-01", "2024-02", "2024-03"]
    # Jan: 150 + 80 + 30 = 260
    assert months[0]["total"] == 260.0
    # Feb: 200 + 120 + 40 = 360
    assert months[1]["total"] == 360.0
    # Mar: 175 + 90 + 35 = 300
    assert months[2]["total"] == 300.0


def test_full_analysis_combines_all(sample_csv: bytes) -> None:
    df = parser.parse_csv(sample_csv)
    result = analytics.full_analysis(df)

    assert "summary" in result
    assert "by_category" in result
    assert "monthly_spending" in result
    assert result["rows_kept"] == 9
    assert result["rows_dropped"] == 0