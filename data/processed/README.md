# Processed Data

This folder contains cleaned and feature-engineered outputs generated from `data/raw/books_goodreads.csv`.

## Folder Layout

```text
data/processed/
├── core/
│   └── books_cleaned.csv
├── analysis/
│   ├── books_analysis.csv
│   ├── books_work_level.csv
│   └── books_themed.csv
├── bridge/
│   ├── book_genres.csv
│   └── book_themes.csv
└── reference/
    ├── cleaning_summary.csv
    ├── data_dictionary.csv
    └── theme_summary.csv
```

## Run Pipelines

Clean raw data:

```bash
.venv/bin/python scripts/clean_books.py
```

Build theme buckets:

```bash
.venv/bin/python scripts/build_theme_features.py
```

## Files

- `core/books_cleaned.csv`: raw Goodreads rows plus cleaned analysis columns.
- `analysis/books_analysis.csv`: default analysis dataset, filtered to 1997-2024 and deduped by `bookId`.
- `analysis/books_work_level.csv`: stricter work-level dataset for top-book tables, deduped by `title_key`, `author_key`, and `first_publish_year`.
- `analysis/books_themed.csv`: default analysis dataset plus multi-label theme bucket columns.
- `bridge/book_genres.csv`: one row per book/genre pair for genre aggregation.
- `bridge/book_themes.csv`: one row per book/theme pair with fractional theme weights.
- `reference/cleaning_summary.csv`: quick row-count summary of the cleaning results.
- `reference/data_dictionary.csv`: descriptions of the main cleaned columns.
- `reference/theme_summary.csv`: quick counts and aggregate popularity fields by theme.

## Recommended Analysis Bases

```python
books = pd.read_csv("data/processed/analysis/books_themed.csv")
book_genres = pd.read_csv("data/processed/bridge/book_genres.csv")
book_themes = pd.read_csv("data/processed/bridge/book_themes.csv")
```

Use `core/books_cleaned.csv` for auditing raw-vs-cleaned fields. Use `analysis/books_analysis.csv` for default trend analysis before theme features. Use `analysis/books_themed.csv` for theme trend analysis. Use `analysis/books_work_level.csv` only when repeated editions would make ranked tables messy.

Note: raw `bbeScore` is retained from the source file for traceability, but it is not cleaned into an analysis feature because the score is opaque and mostly redundant with `bbeVotes`.

Theme columns are multi-label. A book can belong to more than one theme.
