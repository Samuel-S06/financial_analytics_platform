"""
CSV transaction parser.

Validates uploaded CSV files and converts them into a normalized pandas
DataFrame. Defensive about bad input.

Raises ParseError on failure with a human-readable message.
"""

import io
from datetime import datetime

import pandas as pd

REQUIRED_COLUMNS = {"date", "category", "amount"}


class ParseError(ValueError):
    """Raised when a CSV cannot be parsed into the expected schema."""


def parse_csv(content: bytes) -> pd.DataFrame:
    if not content:
        raise ParseError("Uploaded file is empty.")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except pd.errors.ParserError as exc:
        raise ParseError(f"Could not parse CSV: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ParseError("File is not valid UTF-8 text.") from exc

    if df.empty:
        raise ParseError("CSV has no data rows.")

    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ParseError(
            f"CSV is missing required columns: {sorted(missing)}. "
            f"Required columns are: {sorted(REQUIRED_COLUMNS)}."
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["category"] = df["category"].fillna("").astype(str).str.strip()

    if "description" not in df.columns:
        df["description"] = ""
    else:
        df["description"] = df["description"].fillna("").astype(str)

    before = len(df)
    df = df.dropna(subset=["date", "amount"])
    df = df[df["amount"] > 0]
    df = df[df["category"] != ""]
    dropped = before - len(df)

    if df.empty:
        raise ParseError(
            f"No valid rows after cleaning ({before} rows had bad dates, "
            "amounts, or categories)."
        )

    df.attrs["rows_kept"] = len(df)
    df.attrs["rows_dropped"] = dropped

    return df[["date", "category", "amount", "description"]].reset_index(drop=True)


def date_range(df: pd.DataFrame) -> tuple[datetime, datetime]:
    return df["date"].min().to_pydatetime(), df["date"].max().to_pydatetime()
