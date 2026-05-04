from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/books-that-evolve-matplotlib")

import matplotlib.pyplot as plt
import pandas as pd

from plot_style import LINE_WIDTH, MARKER_SIZE, PALETTE, SECONDARY_LINE_WIDTH, apply_light_academia_style, color_map


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "processed_books.csv"
OUT_DIR = ROOT / "outputs" / "exploratory"
TABLE_DIR = OUT_DIR / "tables"
CHART_DIR = OUT_DIR / "charts"

ERA_BREAKS = [2009, 2014, 2019]

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

TRACKED_KEYWORDS = [
    "magic",
    "wizard",
    "dragon",
    "kingdom",
    "realm",
    "court",
    "fae",
    "vampire",
    "werewolf",
    "angel",
    "demon",
    "ghost",
    "academy",
    "school",
    "dystopia",
    "rebellion",
    "district",
    "apocalypse",
    "space",
    "alien",
    "robot",
    "love",
    "mate",
    "curse",
    "prophecy",
]

STOPWORDS = {
    "about",
    "after",
    "all",
    "again",
    "against",
    "along",
    "also",
    "always",
    "among",
    "and",
    "another",
    "any",
    "are",
    "around",
    "as",
    "at",
    "away",
    "back",
    "best",
    "because",
    "been",
    "before",
    "being",
    "between",
    "book",
    "books",
    "both",
    "but",
    "by",
    "can",
    "cannot",
    "could",
    "did",
    "do",
    "does",
    "down",
    "each",
    "even",
    "ever",
    "every",
    "everything",
    "for",
    "find",
    "first",
    "from",
    "get",
    "gets",
    "goodreads",
    "had",
    "has",
    "have",
    "her",
    "here",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "life",
    "like",
    "make",
    "may",
    "more",
    "must",
    "new",
    "no",
    "not",
    "now",
    "of",
    "on",
    "one",
    "only",
    "or",
    "other",
    "over",
    "out",
    "own",
    "read",
    "reads",
    "series",
    "she",
    "she's",
    "should",
    "some",
    "story",
    "such",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "time",
    "two",
    "up",
    "upon",
    "very",
    "was",
    "way",
    "we",
    "when",
    "where",
    "whether",
    "what",
    "which",
    "while",
    "who",
    "why",
    "will",
    "with",
    "world",
    "would",
    "year",
    "years",
    "you",
    "young",
}


def assign_era(year: int, breaks: list[int], year_min: int, year_max: int) -> str:
    start = year_min
    for break_year in breaks:
        if year < break_year:
            return f"{start}-{break_year - 1}"
        start = break_year
    return f"{start}-{year_max}"


def parse_json_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def tokenize(value: object) -> list[str]:
    words = re.findall(r"[a-z][a-z'-]{2,}", str(value or "").casefold())
    return [word.strip("'") for word in words if word.strip("'") not in STOPWORDS]


def load_books() -> tuple[pd.DataFrame, list[str]]:
    books = pd.read_csv(INPUT_PATH, low_memory=False)
    theme_cols = [
        col
        for col in books.columns
        if col.startswith("theme_") and col not in {"theme_tags", "theme_count"}
    ]
    books[theme_cols] = books[theme_cols].astype(bool)
    books["first_publish_year"] = books["first_publish_year"].astype(int)
    books["popularity_score"] = pd.to_numeric(books["popularity_score"], errors="coerce")
    books["popularity_weight"] = books["popularity_score"] - books["popularity_score"].min() + 0.001
    books["active_theme_count"] = books[theme_cols].sum(axis=1).clip(lower=1)
    books["fractional_popularity_weight"] = books["popularity_weight"] / books["active_theme_count"]

    year_min = int(books["first_publish_year"].min())
    year_max = int(books["first_publish_year"].max())
    books["data_driven_era"] = books["first_publish_year"].apply(
        lambda year: assign_era(int(year), ERA_BREAKS, year_min, year_max)
    )
    return books, theme_cols


def build_theme_long(books: pd.DataFrame, theme_cols: list[str]) -> pd.DataFrame:
    id_vars = [
        "bookId",
        "title_clean",
        "primary_author",
        "first_publish_year",
        "data_driven_era",
        "audience",
        "series_flag",
        "popularity_score",
        "popularity_weight",
        "fractional_popularity_weight",
        "active_theme_count",
    ]
    id_vars.extend(col for col in ["scenario_weight", "scenario_fractional_weight"] if col in books.columns)
    theme_long = books.melt(
        id_vars=id_vars,
        value_vars=theme_cols,
        var_name="theme",
        value_name="has_theme",
    )
    theme_long = theme_long.loc[theme_long["has_theme"]].copy()
    theme_long["theme_label"] = theme_long["theme"].map(THEME_LABELS)
    return theme_long


def save_bar(series: pd.Series, path: Path, title: str, xlabel: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    series.plot(kind="bar", ax=ax, color=PALETTE[: len(series)])
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def export_basic_distributions(books: pd.DataFrame, theme_long: pd.DataFrame) -> None:
    books_by_year = books["first_publish_year"].value_counts().sort_index().rename_axis("year").reset_index(name="book_count")
    books_by_age = books["audience"].value_counts().rename_axis("audience").reset_index(name="book_count")
    books_by_theme = (
        theme_long["theme_label"].value_counts().rename_axis("theme").reset_index(name="book_count")
    )
    score_summary = books["popularity_score"].describe(percentiles=[0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])

    books_by_year.to_csv(TABLE_DIR / "basic_books_by_year.csv", index=False)
    books_by_age.to_csv(TABLE_DIR / "basic_books_by_age_group.csv", index=False)
    books_by_theme.to_csv(TABLE_DIR / "basic_books_by_theme.csv", index=False)
    score_summary.to_frame("popularity_score").to_csv(TABLE_DIR / "basic_popularity_score_distribution.csv")

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(
        books_by_year["year"],
        books_by_year["book_count"],
        marker="o",
        markersize=MARKER_SIZE,
        linewidth=SECONDARY_LINE_WIDTH,
        color=PALETTE[0],
    )
    ax.set_title("Books by First Publication Year", fontsize=14, pad=12)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Book count")
    ax.set_xlim(books_by_year["year"].min(), books_by_year["year"].max())
    plt.tight_layout()
    fig.savefig(CHART_DIR / "basic_books_by_year.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    save_bar(
        books["audience"].value_counts(),
        CHART_DIR / "basic_books_by_age_group.png",
        "Books by Age Group",
        "Age group",
        "Book count",
    )
    save_bar(
        theme_long["theme_label"].value_counts(),
        CHART_DIR / "basic_books_by_theme.png",
        "Books by Theme",
        "Theme",
        "Book count",
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.hist(books["popularity_score"].dropna(), bins=60, color=PALETTE[4], edgecolor="white")
    ax.set_title("Popularity Score Distribution", fontsize=14, pad=12)
    ax.set_xlabel("Popularity score")
    ax.set_ylabel("Book count")
    plt.tight_layout()
    fig.savefig(CHART_DIR / "basic_popularity_score_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def export_theme_trends(theme_long: pd.DataFrame) -> pd.DataFrame:
    annual_theme = (
        theme_long.groupby(["first_publish_year", "theme_label"], as_index=False)
        .agg(
            book_count=("bookId", "nunique"),
            weighted_popularity=("fractional_popularity_weight", "sum"),
            avg_popularity_score=("popularity_score", "mean"),
        )
        .sort_values(["first_publish_year", "theme_label"])
    )
    totals = (
        annual_theme.groupby("first_publish_year", as_index=False)["weighted_popularity"]
        .sum()
        .rename(columns={"weighted_popularity": "year_weighted_popularity"})
    )
    annual_theme = annual_theme.merge(totals, on="first_publish_year", how="left")
    annual_theme["popularity_share"] = annual_theme["weighted_popularity"] / annual_theme["year_weighted_popularity"]
    annual_theme["popularity_share_pct"] = annual_theme["popularity_share"] * 100
    annual_theme.to_csv(TABLE_DIR / "theme_trends_by_year.csv", index=False)

    count_by_year = annual_theme.pivot(index="first_publish_year", columns="theme_label", values="book_count").fillna(0)
    share_by_year = annual_theme.pivot(index="first_publish_year", columns="theme_label", values="popularity_share").fillna(0)
    weighted_by_year = annual_theme.pivot(
        index="first_publish_year", columns="theme_label", values="weighted_popularity"
    ).fillna(0)
    theme_colors = color_map(count_by_year.columns)

    fig, ax = plt.subplots(figsize=(14, 7))
    for theme in count_by_year.columns:
        ax.plot(count_by_year.index, count_by_year[theme], linewidth=SECONDARY_LINE_WIDTH, label=theme, color=theme_colors[theme])
    ax.set_title("Book Count by Theme Over Time", fontsize=14, pad=12)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Book count")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_count_by_year.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 7))
    for theme in weighted_by_year.columns:
        ax.plot(weighted_by_year.index, weighted_by_year[theme], linewidth=SECONDARY_LINE_WIDTH, label=theme, color=theme_colors[theme])
    ax.set_title("Weighted Popularity by Theme Over Time", fontsize=14, pad=12)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Weighted popularity")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_weighted_popularity_by_year.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 7))
    for theme in share_by_year.columns:
        ax.plot(share_by_year.index, share_by_year[theme], linewidth=LINE_WIDTH, label=theme, color=theme_colors[theme])
    ax.set_title("Popularity Share by Theme Over Time", fontsize=14, pad=12)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Share of annual weighted popularity")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "theme_popularity_share_core_trend.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return annual_theme


def export_era_defining_tables(books: pd.DataFrame, theme_long: pd.DataFrame) -> None:
    top_books = (
        books.sort_values(["data_driven_era", "popularity_score"], ascending=[True, False])
        .groupby("data_driven_era")
        .head(12)
        [[
            "data_driven_era",
            "first_publish_year",
            "title_clean",
            "primary_author",
            "series",
            "series_flag",
            "audience",
            "popularity_score",
            "theme_tags",
        ]]
    )
    top_authors = (
        books.groupby(["data_driven_era", "primary_author"], as_index=False)
        .agg(
            book_count=("bookId", "nunique"),
            weighted_popularity=("popularity_weight", "sum"),
            avg_popularity_score=("popularity_score", "mean"),
        )
        .sort_values(["data_driven_era", "weighted_popularity"], ascending=[True, False])
        .groupby("data_driven_era")
        .head(12)
    )
    top_themes = (
        theme_long.groupby(["data_driven_era", "theme_label"], as_index=False)
        .agg(
            book_count=("bookId", "nunique"),
            weighted_popularity=("fractional_popularity_weight", "sum"),
            avg_popularity_score=("popularity_score", "mean"),
        )
    )
    era_totals = (
        top_themes.groupby("data_driven_era", as_index=False)["weighted_popularity"]
        .sum()
        .rename(columns={"weighted_popularity": "era_weighted_popularity"})
    )
    top_themes = top_themes.merge(era_totals, on="data_driven_era", how="left")
    top_themes["popularity_share"] = top_themes["weighted_popularity"] / top_themes["era_weighted_popularity"]
    top_themes = top_themes.sort_values(["data_driven_era", "popularity_share"], ascending=[True, False])

    top_books.to_csv(TABLE_DIR / "era_top_books.csv", index=False)
    top_authors.to_csv(TABLE_DIR / "era_top_authors.csv", index=False)
    top_themes.to_csv(TABLE_DIR / "era_top_themes.csv", index=False)

    era_summary = (
        books.groupby("data_driven_era", as_index=False)
        .agg(
            book_count=("bookId", "nunique"),
            avg_popularity_score=("popularity_score", "mean"),
            blockbuster_franchise_books=("series_flag", lambda s: int(s.eq("blockbuster_franchise").sum())),
        )
    )
    theme_blurbs = (
        top_themes.groupby("data_driven_era")
        .head(3)
        .groupby("data_driven_era")
        .apply(lambda group: "; ".join(f"{r.theme_label} ({r.popularity_share:.1%})" for r in group.itertuples()), include_groups=False)
        .rename("top_themes")
        .reset_index()
    )
    author_blurbs = (
        top_authors.groupby("data_driven_era")
        .head(5)
        .groupby("data_driven_era")
        .apply(lambda group: "; ".join(f"{r.primary_author} ({r.book_count})" for r in group.itertuples()), include_groups=False)
        .rename("top_authors")
        .reset_index()
    )
    era_summary = era_summary.merge(theme_blurbs, on="data_driven_era", how="left").merge(
        author_blurbs, on="data_driven_era", how="left"
    )
    era_summary.to_csv(TABLE_DIR / "era_summary_exploratory.csv", index=False)


def keyword_rows(books: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in books.itertuples(index=False):
        text = f"{row.title_key} {row.description_clean}"
        tokens = tokenize(text)
        counts = Counter(tokens)
        for keyword in TRACKED_KEYWORDS:
            count = counts[keyword]
            if count:
                rows.append(
                    {
                        "bookId": row.bookId,
                        "first_publish_year": row.first_publish_year,
                        "data_driven_era": row.data_driven_era,
                        "keyword": keyword,
                        "keyword_count": count,
                        "weighted_keyword_count": count * row.popularity_weight,
                    }
                )
    return pd.DataFrame(rows)


def export_keyword_evolution(books: pd.DataFrame) -> None:
    tracked = keyword_rows(books)
    if tracked.empty:
        return

    keyword_year = (
        tracked.groupby(["first_publish_year", "keyword"], as_index=False)
        .agg(
            book_mentions=("bookId", "nunique"),
            keyword_count=("keyword_count", "sum"),
            weighted_keyword_count=("weighted_keyword_count", "sum"),
        )
        .sort_values(["first_publish_year", "keyword"])
    )
    keyword_year.to_csv(TABLE_DIR / "keyword_trends_by_year.csv", index=False)

    keyword_era = (
        tracked.groupby(["data_driven_era", "keyword"], as_index=False)
        .agg(
            book_mentions=("bookId", "nunique"),
            keyword_count=("keyword_count", "sum"),
            weighted_keyword_count=("weighted_keyword_count", "sum"),
        )
        .sort_values(["data_driven_era", "weighted_keyword_count"], ascending=[True, False])
    )
    keyword_era.to_csv(TABLE_DIR / "keyword_trends_by_era.csv", index=False)

    year_pivot = keyword_year.pivot(index="first_publish_year", columns="keyword", values="weighted_keyword_count").fillna(0)
    top_keywords = keyword_era.groupby("keyword")["weighted_keyword_count"].sum().sort_values(ascending=False).head(12).index
    keyword_colors = color_map(top_keywords)
    fig, ax = plt.subplots(figsize=(14, 7))
    for keyword in top_keywords:
        ax.plot(year_pivot.index, year_pivot[keyword], linewidth=SECONDARY_LINE_WIDTH, label=keyword, color=keyword_colors[keyword])
    ax.set_title("Tracked Keyword Popularity Over Time", fontsize=14, pad=12)
    ax.set_xlabel("First publication year")
    ax.set_ylabel("Weighted keyword count")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
    plt.tight_layout()
    fig.savefig(CHART_DIR / "keyword_weighted_trends_by_year.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    token_rows = []
    for row in books.itertuples(index=False):
        counts = Counter(tokenize(f"{row.title_key} {row.description_clean}"))
        for word, count in counts.items():
            token_rows.append(
                {
                    "data_driven_era": row.data_driven_era,
                    "word": word,
                    "book_mentions": 1,
                    "count": count,
                    "weighted_count": count * row.popularity_weight,
                }
            )
    tokens = pd.DataFrame(token_rows)
    era_words = (
        tokens.groupby(["data_driven_era", "word"], as_index=False)
        .agg(
            book_mentions=("book_mentions", "sum"),
            count=("count", "sum"),
            weighted_count=("weighted_count", "sum"),
        )
    )
    era_totals = (
        era_words.groupby("data_driven_era", as_index=False)["weighted_count"]
        .sum()
        .rename(columns={"weighted_count": "era_weighted_words"})
    )
    era_words = era_words.merge(era_totals, on="data_driven_era", how="left")
    era_words["weighted_share"] = era_words["weighted_count"] / era_words["era_weighted_words"]
    eras = sorted(era_words["data_driven_era"].unique())
    comparisons = []
    for before, after in zip(eras, eras[1:]):
        before_words = era_words.loc[era_words["data_driven_era"].eq(before), ["word", "weighted_share"]]
        after_words = era_words.loc[era_words["data_driven_era"].eq(after), ["word", "weighted_share", "book_mentions"]]
        comparison = after_words.merge(before_words, on="word", how="outer", suffixes=("_after", "_before")).fillna(0)
        comparison["era_transition"] = f"{before} to {after}"
        comparison["share_change"] = comparison["weighted_share_after"] - comparison["weighted_share_before"]
        comparison = comparison.loc[comparison["book_mentions"].ge(3)]
        comparisons.append(comparison)
    rising_falling = pd.concat(comparisons, ignore_index=True)
    rising_falling = rising_falling.sort_values(["era_transition", "share_change"], ascending=[True, False])
    rising_falling.to_csv(TABLE_DIR / "keyword_rising_falling_by_era.csv", index=False)


def scenario_theme_share(theme_long: pd.DataFrame, scenario_name: str) -> pd.DataFrame:
    grouped = (
        theme_long.groupby(["first_publish_year", "theme_label"], as_index=False)
        .agg(weighted_popularity=("scenario_fractional_weight", "sum"), book_count=("bookId", "nunique"))
    )
    totals = (
        grouped.groupby("first_publish_year", as_index=False)["weighted_popularity"]
        .sum()
        .rename(columns={"weighted_popularity": "year_weighted_popularity"})
    )
    grouped = grouped.merge(totals, on="first_publish_year", how="left")
    grouped["popularity_share"] = grouped["weighted_popularity"] / grouped["year_weighted_popularity"]
    grouped["scenario"] = scenario_name
    return grouped


def export_blockbuster_effect(books: pd.DataFrame, theme_cols: list[str]) -> None:
    cutoff = books["popularity_score"].quantile(0.99)
    scenarios = []

    all_books = books.copy()
    all_books["scenario_weight"] = all_books["popularity_weight"]
    scenarios.append(("all_books", all_books))

    removed = books.loc[books["popularity_score"].lt(cutoff)].copy()
    removed["scenario_weight"] = removed["popularity_weight"]
    scenarios.append(("top_1pct_removed", removed))

    capped = books.copy()
    capped["scenario_weight"] = np.minimum(capped["popularity_score"], cutoff) - books["popularity_score"].min() + 0.001
    scenarios.append(("top_1pct_capped", capped))

    non_franchise = books.loc[books["series_flag"].ne("blockbuster_franchise")].copy()
    non_franchise["scenario_weight"] = non_franchise["popularity_weight"]
    scenarios.append(("non_blockbuster_franchise", non_franchise))

    only_franchise = books.loc[books["series_flag"].eq("blockbuster_franchise")].copy()
    only_franchise["scenario_weight"] = only_franchise["popularity_weight"]
    scenarios.append(("blockbuster_franchise_only", only_franchise))

    rows = []
    for scenario_name, scenario_books in scenarios:
        scenario_books["scenario_fractional_weight"] = scenario_books["scenario_weight"] / scenario_books[theme_cols].sum(axis=1).clip(lower=1)
        scenario_long = build_theme_long(scenario_books, theme_cols)
        rows.append(scenario_theme_share(scenario_long, scenario_name))

    comparison = pd.concat(rows, ignore_index=True)
    comparison.to_csv(TABLE_DIR / "blockbuster_theme_share_comparison.csv", index=False)

    selected = comparison.loc[comparison["scenario"].isin(["all_books", "top_1pct_removed", "non_blockbuster_franchise"])]
    for scenario_name, group in selected.groupby("scenario"):
        pivot = group.pivot(index="first_publish_year", columns="theme_label", values="popularity_share").fillna(0)
        theme_colors = color_map(pivot.columns)
        fig, ax = plt.subplots(figsize=(14, 7))
        for theme in pivot.columns:
            ax.plot(pivot.index, pivot[theme], linewidth=SECONDARY_LINE_WIDTH, label=theme, color=theme_colors[theme])
        ax.set_title(f"Theme Popularity Share: {scenario_name.replace('_', ' ').title()}", fontsize=14, pad=12)
        ax.set_xlabel("First publication year")
        ax.set_ylabel("Share of annual weighted popularity")
        ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False)
        plt.tight_layout()
        fig.savefig(CHART_DIR / f"blockbuster_effect_{scenario_name}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)

    scenario_totals = (
        comparison.groupby(["scenario", "theme_label"], as_index=False)["weighted_popularity"]
        .sum()
        .sort_values(["scenario", "weighted_popularity"], ascending=[True, False])
    )
    scenario_totals.to_csv(TABLE_DIR / "blockbuster_theme_totals_comparison.csv", index=False)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    apply_light_academia_style()

    books, theme_cols = load_books()
    theme_long = build_theme_long(books, theme_cols)

    export_basic_distributions(books, theme_long)
    export_theme_trends(theme_long)
    export_era_defining_tables(books, theme_long)
    export_keyword_evolution(books)
    export_blockbuster_effect(books, theme_cols)

    print(f"Wrote exploratory tables to {TABLE_DIR.relative_to(ROOT)}")
    print(f"Wrote exploratory charts to {CHART_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
