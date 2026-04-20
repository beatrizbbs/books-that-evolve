# Step 2.1 Raw Data Issues

Source profiled: `data/books_goodreads.csv`

## Snapshot

- Rows: 52,478
- Columns: 25
- Columns: `bookId`, `title`, `series`, `author`, `rating`, `description`, `language`, `isbn`, `genres`, `characters`, `bookFormat`, `edition`, `pages`, `publisher`, `publishDate`, `firstPublishDate`, `awards`, `numRatings`, `ratingsByStars`, `likedPercent`, `setting`, `coverImg`, `bbeScore`, `bbeVotes`, `price`

## Major Issues

- Missing or blank values are concentrated in optional metadata:
  - `edition`: 47,523 blank rows, 90.6%
  - `series`: 29,009 blank rows, 55.3%
  - `firstPublishDate`: 21,326 blank rows, 40.6%
  - `price`: 14,365 blank rows, 27.4%
  - `language`: 3,806 blank rows, 7.3%
  - `publisher`: 3,695 blank rows, 7.0%
  - `pages`: 2,347 blank rows, 4.5%
  - `description`: 1,337 blank rows, 2.5%

- Duplicate identifiers need cleanup before entity-level analysis:
  - `bookId`: 108 rows belong to 54 duplicate groups.
  - `title` + `author`: 183 rows belong to 89 duplicate groups.
  - `title` alone: 4,316 rows belong to 1,710 duplicate-title groups, which may include different editions, translations, or unrelated works with the same title.

- ISBN quality is uneven:
  - `9999999999999` appears 4,354 times and should be treated as a placeholder, not a real ISBN.
  - Some non-placeholder ISBNs appear more than once, usually 2 rows each.
  - Some ISBN-like values are not ISBN-13, such as Kindle/ASIN-style values.

- Date formats are mixed and need normalization:
  - `publishDate` includes month-name dates like `April 27th 2010`, year-only dates, month-year dates, `M/D/YY`, blanks, and a smaller set of other patterns.
  - `firstPublishDate` is mostly `M/D/YY`, with many blanks and some month-name dates.
  - Two-digit years are ambiguous. For example, `07/11/60` parses as 2060 with Python's default `%y` rules, but it likely means 1960 for `To Kill a Mockingbird`.
  - Some year values appear implausibly old or future-dated after naive parsing. Add project-specific century rules before using publication year trends.

- Description text quality is usable but needs cleaning:
  - 1,337 descriptions are blank.
  - 98 nonblank descriptions are 20 characters or shorter.
  - Many descriptions have missing spaces after periods, likely from scraped paragraph joins.
  - Very long descriptions exist, with the longest around 24k characters.

- Genres are parseable but semantically noisy:
  - `genres` is stored as a Python-list-like string, not normalized relational data.
  - 4,623 rows contain an empty list.
  - Most non-empty rows have up to 10 genres.
  - Top genres include broad categories such as `Fiction`, `Romance`, `Fantasy`, `Young Adult`, `Contemporary`, and `Nonfiction`.

- Numeric columns need light coercion rules:
  - `pages` has 23 nonblank values such as `1 page` instead of plain numbers.
  - `price` has 12 malformed values such as `1.189.88`.
  - `bbeVotes` has a minimum of `-4`, which is suspicious for a vote count.

## Recommended Cleaning Before Analysis

1. Treat empty strings as missing values.
2. Treat ISBN `9999999999999` as missing.
3. Normalize list-like columns with `ast.literal_eval`: `genres`, `characters`, `awards`, `ratingsByStars`, and `setting`.
4. Create canonical duplicate keys using normalized `title`, `author`, and cleaned ISBN.
5. Parse dates with explicit rules for month-name strings, ordinal suffixes, year-only values, month-year values, and two-digit-year century correction.
6. Create clean numeric columns for `pages`, `price`, and vote/count fields while preserving the raw columns.
7. Clean description spacing and flag descriptions that are blank, extremely short, or unusually long.
