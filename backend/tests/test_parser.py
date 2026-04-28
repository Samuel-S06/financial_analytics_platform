"""Tests for the CSV parser."""

import pytest

from app.analysis.parser import ParseError, parse_csv


def test_parses_well_formed_csv(sample_csv: bytes) -> None:
    df = parse_csv(sample_csv)
    assert len(df) == 9
    assert set(df.columns) == {"date", "category", "amount", "description"}
    assert df["amount"].sum() == 920.0


def test_drops_invalid_rows(messy_csv: bytes) -> None:
    df = parse_csv(messy_csv)
    assert len(df) == 2


def test_normalizes_column_case() -> None:
    csv = b"Date,Category,Amount\n2024-01-01,Food,10.00\n"
    df = parse_csv(csv)
    assert "date" in df.columns


def test_rejects_empty_file() -> None:
    with pytest.raises(ParseError, match="empty"):
        parse_csv(b"")


def test_rejects_missing_columns(malformed_csv: bytes) -> None:
    with pytest.raises(ParseError, match="missing required columns"):
        parse_csv(malformed_csv)


def test_drops_negative_and_zero_amounts() -> None:
    csv = (
        b"date,category,amount\n"
        b"2024-01-01,A,10.00\n"
        b"2024-01-02,B,0.00\n"
        b"2024-01-03,C,-5.00\n"
    )
    df = parse_csv(csv)
    assert len(df) == 1
