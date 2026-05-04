from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/books-that-evolve-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from plot_style import LINE_WIDTH, MARKER_SIZE, SECONDARY_LINE_WIDTH, apply_light_academia_style, color_map


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed_books.csv"
TABLE_DIR = ROOT / "outputs" / "tables"
CHART_DIR = ROOT / "outputs" / "charts"

FINAL_BREAKS = [2009, 2014, 2019]

THEME_LABELS = {
    "theme_middle_grade_fantasy": "Middle Grade Fantasy",
    "theme_mythology_adventure": "Mythology Adventure",
    "theme_paranormal_supernatural": "Paranormal / Supernatural",
    "theme_paranormal_romance": "Paranormal Romance",
    "theme_dystopian_post_apocalyptic": "Dystopian / Post-Apocalyptic",
    "theme_epic_high_fantasy": "Epic / High Fantasy",
    "theme_romantasy": "Romantasy",
    "theme_science_fiction": "Science Fiction",
}


def assign_era(year: int, breaks: list[int], year_min: int, year_max: int) -> str:
    start = year_min
    for break_year in breaks:
        if year < break_year:
            return f"{start}-{break_year - 1}"
        start = break_year
    return f"{start}-{year_max}"


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    apply_light_academia_style()

    books = pd.read_csv(INPUT_PATH, low_memory=False)
    year_min = int(books["first_publish_year"].min())
    year_max = int(books["first_publish_year"].max())

    theme_cols = [
        col for col in books.columns
        if col.startswith("theme_") and col not in {"theme_tags", "theme_count"}
    ]

    books[theme_cols] = books[theme_cols].astype(bool)
    books["active_theme_count"] = books[theme_cols].sum(axis=1).clip(lower=1)
    books["popularity_weight"] = books["popularity_score"] - books["popularity_score"].min() + 0.001
    books["fractional_popularity_weight"] = books["popularity_weight"] / books["active_theme_count"]

    theme_long = books.melt(
        id_vars=[
            "bookId",
            "title_clean",
            "primary_author",
            "first_publish_year",
            "popularity_score",
            "fractional_popularity_weight",
            "theme_tags",
        ],
        value_vars=theme_cols,
        var_name="theme",
        value_name="has_theme",
    )
    theme_long = theme_long.loc[theme_long["has_theme"]].copy()
    theme_long["theme_label"] = theme_long["theme"].map(THEME_LABELS)

    annual_theme = (
        theme_long
        .groupby(["first_publish_year", "theme_label"], as_index=False)
        .agg(
            theme_popularity=("fractional_popularity_weight", "sum"),
            book_count=("bookId", "nunique"),
            avg_popularity_score=("popularity_score", "mean"),
        )
    )
    annual_totals = (
        annual_theme
        .groupby("first_publish_year", as_index=False)["theme_popularity"]
        .sum()
        .rename(columns={"theme_popularity": "year_popularity"})
    )
    annual_theme = annual_theme.merge(annual_totals, on="first_publish_year", how="left")
    annual_theme["popularity_share"] = annual_theme["theme_popularity"] / annual_theme["year_popularity"]
    annual_theme["popularity_share_pct"] = annual_theme["popularity_share"] * 100

    share_by_year = (
        annual_theme
        .pivot(index="first_publish_year", columns="theme_label", values="popularity_share")
        .fillna(0)
        .sort_index()
    )
    theme_colors = color_map(share_by_year.columns)

    smoothed_shares = share_by_year.rolling(window=5, center=True, min_periods=1).mean()
    yearly_shift = (
        smoothed_shares
        .diff()
        .abs()
        .sum(axis=1)
        .rename("theme_mix_shift")
        .dropna()
        .sort_index()
    )

    books["data_driven_era"] = books["first_publish_year"].apply(
        lambda year: assign_era(int(year), FINAL_BREAKS, year_min, year_max)
    )
    theme_long["data_driven_era"] = theme_long["first_publish_year"].apply(
        lambda year: assign_era(int(year), FINAL_BREAKS, year_min, year_max)
    )

    era_theme = (
        theme_long
        .groupby(["data_driven_era", "theme_label"], as_index=False)
        .agg(
            theme_popularity=("fractional_popularity_weight", "sum"),
            book_count=("bookId", "nunique"),
        )
    )
    era_totals = (
        era_theme
        .groupby("data_driven_era", as_index=False)["theme_popularity"]
        .sum()
        .rename(columns={"theme_popularity": "era_popularity"})
    )
    era_theme = era_theme.merge(era_totals, on="data_driven_era", how="left")
    era_theme["popularity_share"] = era_theme["theme_popularity"] / era_theme["era_popularity"]
    era_theme["popularity_share_pct"] = era_theme["popularity_share"] * 100

    era_summary = (
        era_theme
        .sort_values(["data_driven_era", "popularity_share"], ascending=[True, False])
        .groupby("data_driven_era")
        .head(3)
        .groupby("data_driven_era", as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "top_themes": "; ".join(
                        f"{row.theme_label} ({row.popularity_share_pct:.1f}%)"
                        for row in group.itertuples(index=False)
                    ),
                    "theme_tagged_books": int(group["book_count"].sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
    )

    top_books_by_era = (
        books
        .sort_values(["data_driven_era", "popularity_score"], ascending=[True, False])
        .groupby("data_driven_era")
        .head(8)
        [[
            "data_driven_era",
            "first_publish_year",
            "title_clean",
            "primary_author",
            "popularity_score",
            "theme_tags",
        ]]
    )

    breakpoints = pd.DataFrame(
        {
            "break_year": FINAL_BREAKS,
            "theme_mix_shift": [float(yearly_shift.loc[year]) for year in FINAL_BREAKS],
            "era_after_break": [
                assign_era(year, FINAL_BREAKS, year_min, year_max)
                for year in FINAL_BREAKS
            ],
        }
    )

    annual_theme.to_csv(TABLE_DIR / "annual_theme_popularity_share.csv", index=False)
    era_summary.to_csv(TABLE_DIR / "data_driven_era_summary.csv", index=False)
    top_books_by_era.to_csv(TABLE_DIR / "top_books_by_data_driven_era.csv", index=False)
    breakpoints.to_csv(TABLE_DIR / "data_driven_era_breakpoints.csv", index=False)

    fig, ax = plt.subplots(figsize=(14, 7))
    for theme in share_by_year.columns:
        ax.plot(share_by_year.index, share_by_year[theme], linewidth=LINE_WIDTH, label=theme, color=theme_colors[theme])
    for break_year in FINAL_BREAKS:
        ax.axvline(break_year, color="black", linestyle="--", alpha=0.35)
    ax.set_title("Theme Popularity Share by Publication Year", fontsize=16, pad=14)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Share of annual popularity")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlim(share_by_year.index.min(), share_by_year.index.max())
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_popularity_share_by_year.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.stackplot(
        share_by_year.index,
        [share_by_year[col] for col in share_by_year.columns],
        labels=share_by_year.columns,
        colors=[theme_colors[col] for col in share_by_year.columns],
        alpha=0.92,
    )
    for break_year in FINAL_BREAKS:
        ax.axvline(break_year, color="white", linestyle="--", alpha=0.8, linewidth=1.4)
    ax.set_title("Theme Popularity Mix by Publication Year", fontsize=16, pad=14)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Share of annual popularity")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_xlim(share_by_year.index.min(), share_by_year.index.max())
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_popularity_mix_by_year.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(
        yearly_shift.index,
        yearly_shift,
        marker="o",
        markersize=MARKER_SIZE,
        linewidth=SECONDARY_LINE_WIDTH,
        color=theme_colors[share_by_year.columns[0]],
    )
    for break_year in FINAL_BREAKS:
        ax.axvline(break_year, color="black", linestyle="--", alpha=0.7)
        ax.text(
            break_year + 0.15,
            ax.get_ylim()[1] * 0.93,
            str(break_year),
            rotation=90,
            va="top",
        )
    ax.set_title("Year-to-Year Change in Theme Popularity Mix", fontsize=16, pad=14)
    ax.set_xlabel("Year")
    ax.set_ylabel("Total absolute share shift")
    ax.set_xlim(share_by_year.index.min(), share_by_year.index.max())
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_mix_shift_breakpoints.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {TABLE_DIR.relative_to(ROOT) / 'annual_theme_popularity_share.csv'}")
    print(f"Wrote {TABLE_DIR.relative_to(ROOT) / 'data_driven_era_summary.csv'}")
    print(f"Wrote {TABLE_DIR.relative_to(ROOT) / 'top_books_by_data_driven_era.csv'}")
    print(f"Wrote {TABLE_DIR.relative_to(ROOT) / 'data_driven_era_breakpoints.csv'}")
    print(f"Wrote {CHART_DIR.relative_to(ROOT) / 'theme_popularity_share_by_year.png'}")
    print(f"Wrote {CHART_DIR.relative_to(ROOT) / 'theme_popularity_mix_by_year.png'}")
    print(f"Wrote {CHART_DIR.relative_to(ROOT) / 'theme_mix_shift_breakpoints.png'}")


if __name__ == "__main__":
    main()
