from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "scope_books.csv"
OUT_PATH = ROOT / "data" / "processed_books.csv"
SUMMARY_PATH = ROOT / "data" / "reference" / "popularity_score_summary.csv"

WEIGHTS = {
    "log_numRatings_z": 0.5,
    "averageRating_z": 0.3,
    "log_bbeVotes_z": 0.2,
}


def zscore(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def add_score(scope: pd.DataFrame) -> pd.DataFrame:
    df = scope.copy()
    num_ratings = pd.to_numeric(df["numRatings_clean"], errors="coerce").fillna(0)
    avg_rating = pd.to_numeric(df["averageRating"], errors="coerce")
    bbe_votes = pd.to_numeric(df["bbeVotes_clean"], errors="coerce").fillna(0)

    df["log_numRatings"] = np.log1p(num_ratings)
    df["log_bbeVotes"] = np.log1p(bbe_votes)
    df["log_numRatings_z"] = zscore(df["log_numRatings"])
    df["averageRating_z"] = zscore(avg_rating)
    df["log_bbeVotes_z"] = zscore(df["log_bbeVotes"])
    df["popularity_score"] = (
        WEIGHTS["log_numRatings_z"] * df["log_numRatings_z"]
        + WEIGHTS["averageRating_z"] * df["averageRating_z"]
        + WEIGHTS["log_bbeVotes_z"] * df["log_bbeVotes_z"]
    )
    df["popularity_rank"] = df["popularity_score"].rank(method="dense", ascending=False).astype("Int64")
    return df.sort_values("popularity_rank").reset_index(drop=True)


def build_summary(processed: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("processed_rows", len(processed)),
            ("missing_numRatings_clean_treated_as_zero", int(processed["numRatings_clean"].isna().sum())),
            ("missing_bbeVotes_clean_treated_as_zero", int(processed["bbeVotes_clean"].isna().sum())),
            ("missing_averageRating", int(processed["averageRating"].isna().sum())),
            ("popularity_score_min", processed["popularity_score"].min()),
            ("popularity_score_median", processed["popularity_score"].median()),
            ("popularity_score_max", processed["popularity_score"].max()),
            ("weight_log_numRatings_z", WEIGHTS["log_numRatings_z"]),
            ("weight_averageRating_z", WEIGHTS["averageRating_z"]),
            ("weight_log_bbeVotes_z", WEIGHTS["log_bbeVotes_z"]),
        ],
        columns=["metric", "value"],
    )


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    scope = pd.read_csv(INPUT_PATH, low_memory=False)
    processed = add_score(scope)
    processed.to_csv(OUT_PATH, index=False)
    build_summary(processed).to_csv(SUMMARY_PATH, index=False)
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
