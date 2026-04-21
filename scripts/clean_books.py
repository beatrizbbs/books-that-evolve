from __future__ import annotations

import ast
import html
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


PROJECT_START_YEAR = 1997
PROJECT_END_YEAR = 2024
MIN_VALID_PUBLICATION_YEAR = 1450

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = ROOT / "data" / "raw" / "books_goodreads.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CORE_DIR = PROCESSED_DIR / "core"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
BRIDGE_DIR = PROCESSED_DIR / "bridge"
REFERENCE_DIR = PROCESSED_DIR / "reference"
CLEANED_DATA_PATH = CORE_DIR / "books_cleaned.csv"
ANALYSIS_DATA_PATH = ANALYSIS_DIR / "books_analysis.csv"
WORK_LEVEL_DATA_PATH = ANALYSIS_DIR / "books_work_level.csv"
GENRES_DATA_PATH = BRIDGE_DIR / "book_genres.csv"
SUMMARY_PATH = REFERENCE_DIR / "cleaning_summary.csv"
DATA_DICTIONARY_PATH = REFERENCE_DIR / "data_dictionary.csv"

CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")
ROLE_LABEL_RE = re.compile(r"\s*\([^)]*\)")
TWO_DIGIT_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2})$")
FOUR_DIGIT_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
YEAR_ONLY_RE = re.compile(r"^(\d{4})$")
YEAR_RE = re.compile(r"(\d{4})")
ISBN10_RE = re.compile(r"^(?:\d{9}[\dXx])$")
ISBN13_RE = re.compile(r"^(?:\d{13})$")
ASIN_RE = re.compile(r"^B[A-Z0-9]{9}$")


def normalize_whitespace(value: object) -> str:
    value = str(value or "")
    value = CONTROL_CHARS_RE.sub(" ", value)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip()


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def make_text_key(value: object) -> str:
    value = normalize_whitespace(value).casefold()
    value = strip_accents(value)
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return normalize_whitespace(value)


def parse_list_field(value: object) -> list[str]:
    value = normalize_whitespace(value)
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [normalize_whitespace(item) for item in parsed if normalize_whitespace(item)]


def split_author_contributors(author_value: object) -> list[str]:
    contributors: list[str] = []
    current: list[str] = []
    depth = 0

    for char in str(author_value or ""):
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1

        if char == "," and depth == 0:
            contributors.append("".join(current))
            current = []
        else:
            current.append(char)

    contributors.append("".join(current))
    return [normalize_whitespace(part) for part in contributors if normalize_whitespace(part)]


def clean_author_name(value: object) -> str:
    value = normalize_whitespace(value)
    value = ROLE_LABEL_RE.sub("", value)
    return normalize_whitespace(value)


def normalize_date_text(value: object) -> str:
    value = normalize_whitespace(value)
    value = re.sub(r"(\d)(st|nd|rd|th)", r"\1", value)
    return normalize_whitespace(value)


def infer_two_digit_year(
    two_digit_year: str,
    edition_publish_year: int | pd.NA = None,
) -> tuple[int, str]:
    yy = int(two_digit_year)
    year_2000 = 2000 + yy
    year_1900 = 1900 + yy

    can_be_modern = PROJECT_START_YEAR <= year_2000 <= PROJECT_END_YEAR
    if edition_publish_year is not None and pd.notna(edition_publish_year):
        can_be_modern = can_be_modern and year_2000 <= int(edition_publish_year) + 1

    if can_be_modern:
        return year_2000, "two_digit_year_inferred_modern"
    return year_1900, "two_digit_year_inferred_pre_2000"


def parse_publication_year(
    value: object,
    edition_publish_year: int | pd.NA = None,
) -> tuple[int | pd.NA, str]:
    value = normalize_date_text(value)
    if not value:
        return pd.NA, "missing_raw_date"

    two_digit_match = TWO_DIGIT_DATE_RE.match(value)
    if two_digit_match:
        return infer_two_digit_year(two_digit_match.group(3), edition_publish_year)

    four_digit_match = FOUR_DIGIT_DATE_RE.match(value)
    if four_digit_match:
        return int(four_digit_match.group(3)), "parsed_four_digit_slash_date"

    year_only_match = YEAR_ONLY_RE.match(value)
    if year_only_match:
        return int(year_only_match.group(1)), "parsed_year_only"

    parsed = pd.to_datetime(pd.Series([value]), errors="coerce", format="mixed").iloc[0]
    if pd.notna(parsed):
        return int(parsed.year), "parsed_text_date"

    year_match = YEAR_RE.search(value)
    if year_match:
        return int(year_match.group(1)), "parsed_year_from_unrecognized_text"

    return pd.NA, "unparseable_raw_date"


def add_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    edition_year_results = df["publishDate"].apply(parse_publication_year)
    df["publish_year_for_disambiguation"] = pd.array(
        [year for year, _ in edition_year_results],
        dtype="Int64",
    )
    df["publish_year_parse_status"] = [status for _, status in edition_year_results]

    def choose_first_publish_year(row: pd.Series) -> pd.Series:
        first_raw = row["firstPublishDate"]
        publish_raw = row["publishDate"]
        edition_year = row["publish_year_for_disambiguation"]

        if normalize_date_text(first_raw):
            year, parse_status = parse_publication_year(first_raw, edition_year)
            source = "firstPublishDate"
        elif normalize_date_text(publish_raw):
            year, parse_status = parse_publication_year(publish_raw)
            source = "publishDate_fallback"
            parse_status = f"missing_firstPublishDate__{parse_status}"
        else:
            year, parse_status, source = pd.NA, "missing_both_date_fields", "missing"

        invalid_reason = ""
        clean_year = year
        if pd.isna(year):
            invalid_reason = "missing_or_unparseable_year"
        elif int(year) < MIN_VALID_PUBLICATION_YEAR:
            invalid_reason = "before_min_valid_publication_year"
            clean_year = pd.NA
        elif int(year) > PROJECT_END_YEAR:
            invalid_reason = "after_project_end_year"
            clean_year = pd.NA

        return pd.Series(
            {
                "first_publish_year_raw_parsed": year,
                "first_publish_year": clean_year,
                "first_publish_year_source": source,
                "first_publish_year_parse_status": parse_status,
                "first_publish_year_invalid_reason": invalid_reason,
            }
        )

    first_year_columns = df.apply(choose_first_publish_year, axis=1)
    df = pd.concat([df, first_year_columns], axis=1)
    df["first_publish_year"] = pd.array(df["first_publish_year"], dtype="Int64")
    df["first_publish_year_raw_parsed"] = pd.array(
        df["first_publish_year_raw_parsed"],
        dtype="Int64",
    )
    df["first_publish_year_missing"] = df["first_publish_year"].isna()
    df["first_publish_year_uses_fallback"] = df["first_publish_year_source"].eq(
        "publishDate_fallback"
    )
    df["first_publish_year_two_digit_inferred"] = df[
        "first_publish_year_parse_status"
    ].str.contains("two_digit_year", regex=False)
    df["in_project_scope_1997_2024"] = df["first_publish_year"].between(
        PROJECT_START_YEAR,
        PROJECT_END_YEAR,
    )
    return df


def add_title_author_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["title_clean"] = df["title"].map(normalize_whitespace).astype("string")
    df["title_key"] = df["title_clean"].map(make_text_key).astype("string")
    df["title_has_subtitle"] = df["title_clean"].str.contains(":", regex=False)
    df["title_has_bracket_note"] = df["title_clean"].str.contains(
        r"\[[^\]]+\]|\([^\)]+\)",
        regex=True,
    )
    df["title_clean_changed"] = df["title_clean"].ne(df["title"])

    author_contributors = df["author"].map(split_author_contributors)
    cleaned_contributors = author_contributors.map(
        lambda parts: [clean_author_name(part) for part in parts if clean_author_name(part)]
    )

    df["author_clean"] = cleaned_contributors.map(lambda parts: ", ".join(parts)).astype(
        "string"
    )
    df["primary_author"] = cleaned_contributors.map(
        lambda parts: parts[0] if parts else pd.NA
    ).astype("string")
    df["author_key"] = df["primary_author"].fillna("").map(make_text_key).astype("string")
    df["author_contributors_count"] = cleaned_contributors.map(len).astype("Int64")
    df["author_had_role_labels"] = df["author"].str.contains(r"\([^)]*\)", regex=True)
    df["author_clean_changed"] = df["author_clean"].ne(df["author"])
    return df


def add_genre_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    parsed_genres = df["genres"].map(parse_list_field)
    cleaned_genres = parsed_genres.map(lambda items: [normalize_whitespace(item) for item in items])

    df["genres_clean"] = cleaned_genres.map(lambda items: json.dumps(items, ensure_ascii=False))
    df["genres_key"] = cleaned_genres.map(
        lambda items: json.dumps([make_text_key(item) for item in items], ensure_ascii=False)
    )
    df["genre_count"] = cleaned_genres.map(len).astype("Int64")
    df["primary_genre"] = cleaned_genres.map(lambda items: items[0] if items else pd.NA).astype(
        "string"
    )
    df["genres_missing"] = df["genre_count"].eq(0)

    genre_keys = cleaned_genres.map(lambda items: {make_text_key(item) for item in items})
    youth_keys = {"young adult", "teen", "middle grade", "childrens"}
    df["has_youth_genre"] = genre_keys.map(lambda keys: bool(keys & youth_keys))
    return df


def add_description_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def clean_description(value: object) -> str:
        value = html.unescape(str(value or ""))
        value = CONTROL_CHARS_RE.sub(" ", value)
        value = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", value)
        return normalize_whitespace(value)

    df["description_clean"] = df["description"].map(clean_description).astype("string")
    df["description_missing"] = df["description_clean"].str.strip().eq("")
    df["description_char_count"] = df["description_clean"].str.len().astype("Int64")
    df["description_word_count"] = (
        df["description_clean"]
        .str.findall(r"\b\w+\b")
        .map(len)
        .astype("Int64")
    )
    df["description_short"] = df["description_word_count"].lt(20)
    df["description_clean_changed"] = df["description_clean"].ne(df["description"])
    return df


def clean_numeric_series(
    series: pd.Series,
    *,
    valid_min: float | None = None,
    valid_max: float | None = None,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    raw = series.fillna("").str.strip()
    numeric = pd.to_numeric(raw.str.replace(",", "", regex=False), errors="coerce")
    nonblank = raw.ne("")
    invalid = nonblank & numeric.isna()
    if valid_min is not None:
        invalid = invalid | numeric.lt(valid_min)
    if valid_max is not None:
        invalid = invalid | numeric.gt(valid_max)
    numeric = numeric.mask(invalid)
    return numeric, raw.eq(""), invalid


def add_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_specs = {
        "rating": ("averageRating", 0, 5),
        "numRatings": ("numRatings_clean", 0, None),
        "bbeVotes": ("bbeVotes_clean", 0, None),
        "likedPercent": ("likedPercent_clean", 0, 100),
        "pages": ("pages_clean", 0, None),
        "price": ("price_clean", 0, None),
    }

    for raw_col, (clean_col, valid_min, valid_max) in numeric_specs.items():
        numeric, missing, invalid = clean_numeric_series(
            df[raw_col],
            valid_min=valid_min,
            valid_max=valid_max,
        )
        if clean_col in {"numRatings_clean", "bbeVotes_clean", "pages_clean"}:
            df[clean_col] = pd.array(numeric.round(), dtype="Int64")
        else:
            df[clean_col] = numeric
        df[f"{clean_col}_missing"] = missing
        df[f"{clean_col}_invalid"] = invalid

    return df


def add_isbn_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    isbn_clean = df["isbn"].fillna("").str.strip().str.replace("-", "", regex=False)
    isbn_clean = isbn_clean.str.replace(" ", "", regex=False)
    isbn_clean = isbn_clean.mask(isbn_clean.eq("9999999999999"), "")
    isbn_upper = isbn_clean.str.upper()

    def classify_isbn(value: str) -> str:
        if not value:
            return "missing_or_placeholder"
        if ISBN13_RE.match(value):
            return "isbn13"
        if ISBN10_RE.match(value):
            return "isbn10"
        if ASIN_RE.match(value.upper()):
            return "asin"
        return "other_identifier"

    df["isbn_clean"] = isbn_clean.astype("string")
    df["isbn_type"] = isbn_upper.map(classify_isbn).astype("string")
    df["isbn_missing_or_placeholder"] = df["isbn_type"].eq("missing_or_placeholder")
    return df


def add_duplicate_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["duplicate_book_id"] = df["bookId"].duplicated(keep=False)
    df["duplicate_title_author_key"] = df[["title_key", "author_key"]].duplicated(keep=False)
    df["duplicate_clean_isbn"] = (
        df["isbn_clean"].ne("") & df["isbn_clean"].duplicated(keep=False)
    )
    return df


def build_genres_long(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        genres = json.loads(row["genres_clean"])
        genre_keys = json.loads(row["genres_key"])
        for order, (genre, genre_key) in enumerate(zip(genres, genre_keys), start=1):
            rows.append(
                {
                    "bookId": row["bookId"],
                    "title_clean": row["title_clean"],
                    "primary_author": row["primary_author"],
                    "first_publish_year": row["first_publish_year"],
                    "genre_order": order,
                    "genre": genre,
                    "genre_key": genre_key,
                }
            )
    return pd.DataFrame(rows)


def build_analysis_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Default dataset for trend analysis: scoped years, exact bookId deduped."""
    return (
        df[df["in_project_scope_1997_2024"]]
        .sort_values(["numRatings_clean", "bbeVotes_clean", "averageRating"], ascending=False)
        .drop_duplicates(["bookId"], keep="first")
        .sort_index()
        .copy()
    )


def build_work_level_dataset(analysis_df: pd.DataFrame) -> pd.DataFrame:
    """Canonical work-level view for top-book tables and cleaner ranked lists."""
    return (
        analysis_df
        .sort_values(["numRatings_clean", "bbeVotes_clean", "averageRating"], ascending=False)
        .drop_duplicates(["title_key", "author_key", "first_publish_year"], keep="first")
        .sort_index()
        .copy()
    )


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    analysis_df = build_analysis_dataset(df)
    work_level_df = build_work_level_dataset(analysis_df)
    return pd.DataFrame(
        {
            "metric": [
                "total_rows",
                "analysis_rows_after_scope_and_book_id_dedupe",
                "work_level_rows_after_title_author_year_dedupe",
                "rows_removed_by_book_id_dedupe_in_scope",
                "rows_removed_by_work_level_dedupe",
                "first_publish_year_present",
                "first_publish_year_missing_after_cleaning",
                "used_publishDate_fallback",
                "two_digit_year_inferred",
                "in_project_scope_1997_2024",
                "blank_title_clean",
                "blank_primary_author",
                "title_clean_changed",
                "author_clean_changed",
                "duplicate_title_author_key_rows",
                "genres_missing",
                "has_youth_genre",
                "description_missing",
                "description_short",
                "description_clean_changed",
                "invalid_averageRating",
                "invalid_numRatings",
                "invalid_bbeVotes",
                "invalid_pages",
                "invalid_price",
                "isbn_missing_or_placeholder",
                "duplicate_clean_isbn_rows",
            ],
            "rows": [
                len(df),
                len(analysis_df),
                len(work_level_df),
                int(df["in_project_scope_1997_2024"].sum() - len(analysis_df)),
                int(len(analysis_df) - len(work_level_df)),
                int(df["first_publish_year"].notna().sum()),
                int(df["first_publish_year"].isna().sum()),
                int(df["first_publish_year_uses_fallback"].sum()),
                int(df["first_publish_year_two_digit_inferred"].sum()),
                int(df["in_project_scope_1997_2024"].sum()),
                int(df["title_clean"].str.strip().eq("").sum()),
                int(df["primary_author"].fillna("").str.strip().eq("").sum()),
                int(df["title_clean_changed"].sum()),
                int(df["author_clean_changed"].sum()),
                int(df[["title_key", "author_key"]].duplicated(keep=False).sum()),
                int(df["genres_missing"].sum()),
                int(df["has_youth_genre"].sum()),
                int(df["description_missing"].sum()),
                int(df["description_short"].sum()),
                int(df["description_clean_changed"].sum()),
                int(df["averageRating_invalid"].sum()),
                int(df["numRatings_clean_invalid"].sum()),
                int(df["bbeVotes_clean_invalid"].sum()),
                int(df["pages_clean_invalid"].sum()),
                int(df["price_clean_invalid"].sum()),
                int(df["isbn_missing_or_placeholder"].sum()),
                int(df["duplicate_clean_isbn"].sum()),
            ],
        }
    )


def build_data_dictionary() -> pd.DataFrame:
    rows = [
        ("first_publish_year", "Cleaned first publication year; invalid/missing values are NA."),
        ("in_project_scope_1997_2024", "True when first_publish_year is inside the README scope."),
        ("title_clean", "Whitespace/control-character cleaned title for display."),
        ("title_key", "Lowercase accent-stripped title key for matching and dedupe."),
        ("author_clean", "Author/contributor string with parenthetical role labels removed."),
        ("primary_author", "First listed cleaned author."),
        ("author_key", "Lowercase accent-stripped primary author key for matching."),
        ("genres_clean", "JSON list of cleaned Goodreads genre labels."),
        ("genres_key", "JSON list of normalized genre keys."),
        ("genre_count", "Number of parsed genres."),
        ("primary_genre", "First Goodreads genre label when present."),
        ("has_youth_genre", "True when genres include young adult, teen, middle grade, or childrens."),
        ("description_clean", "HTML-unescaped, whitespace-normalized description."),
        ("description_word_count", "Word count from description_clean."),
        ("averageRating", "Numeric cleaned version of raw rating."),
        ("numRatings_clean", "Numeric cleaned version of raw numRatings."),
        ("bbeVotes_clean", "Numeric cleaned version of raw bbeVotes; invalid negatives set to NA."),
        ("likedPercent_clean", "Numeric cleaned version of raw likedPercent."),
        ("pages_clean", "Numeric cleaned version of raw pages."),
        ("price_clean", "Numeric cleaned version of raw price."),
        ("isbn_clean", "Clean ISBN/identifier with placeholder 9999999999999 set to blank."),
        ("isbn_type", "Identifier type: isbn13, isbn10, asin, other_identifier, or missing_or_placeholder."),
        ("duplicate_book_id", "True when raw bookId appears more than once."),
        ("duplicate_title_author_key", "True when cleaned title and author keys repeat."),
        ("duplicate_clean_isbn", "True when nonblank cleaned ISBN/identifier repeats."),
        ("analysis/books_analysis.csv", "Default analysis file: 1997-2024 scope and duplicate bookId rows removed."),
        ("analysis/books_work_level.csv", "Canonical work-level file: books_analysis additionally deduped by title_key, author_key, and first_publish_year."),
    ]
    return pd.DataFrame(rows, columns=["column", "description"])


def main() -> None:
    for directory in [CORE_DIR, ANALYSIS_DIR, BRIDGE_DIR, REFERENCE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_DATA_PATH, dtype="string", keep_default_na=False)
    df = add_date_columns(df)
    df = add_title_author_columns(df)
    df = add_genre_columns(df)
    df = add_description_columns(df)
    df = add_numeric_columns(df)
    df = add_isbn_columns(df)
    df = add_duplicate_flags(df)
    analysis_df = build_analysis_dataset(df)
    work_level_df = build_work_level_dataset(analysis_df)
    genres_long = build_genres_long(df)

    df.to_csv(CLEANED_DATA_PATH, index=False)
    analysis_df.to_csv(ANALYSIS_DATA_PATH, index=False)
    work_level_df.to_csv(WORK_LEVEL_DATA_PATH, index=False)
    genres_long.to_csv(GENRES_DATA_PATH, index=False)
    build_summary(df).to_csv(SUMMARY_PATH, index=False)
    build_data_dictionary().to_csv(DATA_DICTIONARY_PATH, index=False)

    print(f"Wrote {CLEANED_DATA_PATH.relative_to(ROOT)}")
    print(f"Wrote {ANALYSIS_DATA_PATH.relative_to(ROOT)}")
    print(f"Wrote {WORK_LEVEL_DATA_PATH.relative_to(ROOT)}")
    print(f"Wrote {GENRES_DATA_PATH.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Wrote {DATA_DICTIONARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
