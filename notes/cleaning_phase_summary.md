# Cleaning Phase Summary

Cleaning pipeline: `scripts/clean_books.py`

Raw input:

- `data/raw/books_goodreads.csv`

Processed outputs:

- `data/processed/core/books_cleaned.csv`
- `data/processed/analysis/books_analysis.csv`
- `data/processed/analysis/books_work_level.csv`
- `data/processed/analysis/books_themed.csv`
- `data/processed/bridge/book_genres.csv`
- `data/processed/bridge/book_themes.csv`
- `data/processed/reference/cleaning_summary.csv`
- `data/processed/reference/data_dictionary.csv`
- `data/processed/reference/theme_summary.csv`

Run:

```bash
.venv/bin/python scripts/clean_books.py
```

## What Was Cleaned

### Publication Dates

- Created `first_publish_year`.
- Uses `firstPublishDate` first.
- Falls back to `publishDate` when `firstPublishDate` is missing.
- Adds flags for fallback years and two-digit year inference.
- Marks missing, unparseable, pre-1450, and post-2024 years as invalid/missing.
- Adds `in_project_scope_1997_2024` for the project time window.

Important caveat: many dates use two-digit years, so older classics can remain ambiguous. These rows are flagged with `first_publish_year_two_digit_inferred`.

### Titles and Authors

- Created `title_clean` and `title_key`.
- Created `author_clean`, `primary_author`, and `author_key`.
- Removed parenthetical role labels from author strings, such as `Goodreads Author`, `Illustrator`, `Translator`, and `Introduction`.
- Preserved raw `title` and `author` columns.
- Added duplicate flags using cleaned title/author keys.

### Genres

- Parsed Goodreads list-like genre strings.
- Created `genres_clean`, `genres_key`, `genre_count`, and `primary_genre`.
- Created `has_youth_genre` for YA, teen, middle grade, and childrens labels.
- Created `book_genres.csv`, an exploded genre table with one row per book/genre pair.

Important caveat: Goodreads genres are reader/platform shelves, not controlled metadata. They should be mapped into project-specific theme buckets before final analysis.

### Descriptions

- Created `description_clean`.
- Normalized whitespace and fixed common scraped paragraph joins like missing spaces after periods.
- Added `description_word_count`, `description_missing`, and `description_short`.

Important caveat: descriptions are useful for keyword/theme extraction but should not be treated as authoritative metadata.

### Numeric Fields

- Created cleaned numeric fields:
  - `averageRating`
  - `numRatings_clean`
  - `bbeVotes_clean`
  - `likedPercent_clean`
  - `pages_clean`
  - `price_clean`
- Invalid values are flagged and set to missing in the cleaned numeric columns.

Important caveat: Goodreads ratings, votes, and scores reflect platform behavior and visibility bias. They are useful for cultural-memory analysis but not market-wide popularity.

Decision update: raw `bbeScore` is retained for traceability, but it is not cleaned into an analysis feature. The field is opaque and mostly redundant with `bbeVotes`, so downstream popularity scoring should use `numRatings_clean`, `averageRating`, and `bbeVotes_clean`.

### ISBN and Duplicate Flags

- Created `isbn_clean`.
- Treats placeholder ISBN `9999999999999` as missing.
- Classifies identifiers with `isbn_type`.
- Adds duplicate flags:
  - `duplicate_book_id`
  - `duplicate_title_author_key`
  - `duplicate_clean_isbn`

## Current Cleaning Summary

- Total rows: 52,478
- Rows with cleaned `first_publish_year`: 51,928
- Missing/invalid `first_publish_year`: 550
- Rows using `publishDate` fallback: 21,069
- Rows with two-digit year inference: 28,968
- Rows in project scope, 1997-2024: 37,327
- Missing genres: 4,623
- Rows with youth-related genre labels: 13,590
- Missing descriptions: 1,337
- Short descriptions: 2,323
- Invalid `bbeVotes`: 52
- Invalid `pages`: 23
- Invalid `price`: 12
- Placeholder/missing ISBNs: 4,354
- Duplicate cleaned title-author key rows: 1,589

## Recommended Analysis Base

Use `books_themed.csv` as the main analysis dataset once theme features are built.

For time-based analysis:

```python
books = pd.read_csv("data/processed/analysis/books_themed.csv")
```

For genre aggregation:

```python
book_genres = pd.read_csv("data/processed/bridge/book_genres.csv")
book_themes = pd.read_csv("data/processed/bridge/book_themes.csv")
```

## Remaining Decisions

- Build project-specific theme buckets from `genres_clean`, `title_clean`, and `description_clean`.
- Decide whether to deduplicate exact repeated works before trend analysis.
- Decide how much to rely on fallback publication years.
- Treat raw `bbeScore` as ignored for analysis unless it is needed for a one-off audit.
