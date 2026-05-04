from __future__ import annotations

import ast
import html
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "books_goodreads.csv"
OUT_PATH = ROOT / "data" / "clean_books.csv"
SUMMARY_PATH = ROOT / "data" / "reference" / "cleaning_summary.csv"

PROJECT_START_YEAR = 1997
PROJECT_END_YEAR = 2024
MIN_VALID_PUBLICATION_YEAR = 1450

CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
SPACE_RE = re.compile(r"\s+")
ROLE_RE = re.compile(r"\s*\([^)]*\)")
TWO_DIGIT_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2})$")
FOUR_DIGIT_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
YEAR_ONLY_RE = re.compile(r"^(\d{4})$")
YEAR_RE = re.compile(r"(\d{4})")
ISBN10_RE = re.compile(r"^(?:\d{9}[\dXx])$")
ISBN13_RE = re.compile(r"^(?:\d{13})$")
ASIN_RE = re.compile(r"^B[A-Z0-9]{9}$")


def clean_space(value: object) -> str:
    value = str(value or "")
    value = CONTROL_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip()


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def make_key(value: object) -> str:
    value = strip_accents(clean_space(value).casefold())
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return clean_space(value)


def parse_list(value: object) -> list[str]:
    value = clean_space(value)
    if not value:
        return []
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [clean_space(item) for item in parsed if clean_space(item)]


def split_contributors(author: object) -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    depth = 0
    for char in str(author or ""):
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        if char == "," and depth == 0:
            pieces.append("".join(current))
            current = []
        else:
            current.append(char)
    pieces.append("".join(current))
    return [clean_space(piece) for piece in pieces if clean_space(piece)]


def clean_author(value: object) -> str:
    return clean_space(ROLE_RE.sub("", clean_space(value)))


def normalize_date(value: object) -> str:
    value = clean_space(value)
    value = re.sub(r"(\d)(st|nd|rd|th)", r"\1", value)
    return clean_space(value)


def infer_two_digit_year(two_digit: str, edition_year: int | pd.NA = None) -> tuple[int, str]:
    yy = int(two_digit)
    year_2000 = 2000 + yy
    year_1900 = 1900 + yy
    can_be_modern = PROJECT_START_YEAR <= year_2000 <= PROJECT_END_YEAR
    if edition_year is not None and pd.notna(edition_year):
        can_be_modern = can_be_modern and year_2000 <= int(edition_year) + 1
    if can_be_modern:
        return year_2000, "two_digit_year_inferred_modern"
    return year_1900, "two_digit_year_inferred_pre_2000"


def parse_year(value: object, edition_year: int | pd.NA = None) -> tuple[int | pd.NA, str]:
    value = normalize_date(value)
    if not value:
        return pd.NA, "missing_raw_date"
    match = TWO_DIGIT_DATE_RE.match(value)
    if match:
        return infer_two_digit_year(match.group(3), edition_year)
    match = FOUR_DIGIT_DATE_RE.match(value)
    if match:
        return int(match.group(3)), "parsed_four_digit_slash_date"
    match = YEAR_ONLY_RE.match(value)
    if match:
        return int(match.group(1)), "parsed_year_only"
    parsed = pd.to_datetime(pd.Series([value]), errors="coerce", format="mixed").iloc[0]
    if pd.notna(parsed):
        return int(parsed.year), "parsed_text_date"
    match = YEAR_RE.search(value)
    if match:
        return int(match.group(1)), "parsed_year_from_text"
    return pd.NA, "unparseable_raw_date"


def clean_description(value: object) -> str:
    value = html.unescape(str(value or ""))
    value = CONTROL_RE.sub(" ", value)
    value = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", value)
    return clean_space(value)


def clean_numeric(series: pd.Series, *, min_value: float | None = None, max_value: float | None = None) -> pd.Series:
    raw = series.fillna("").str.strip()
    numeric = pd.to_numeric(raw.str.replace(",", "", regex=False), errors="coerce")
    invalid = raw.ne("") & numeric.isna()
    if min_value is not None:
        invalid = invalid | numeric.lt(min_value)
    if max_value is not None:
        invalid = invalid | numeric.gt(max_value)
    return numeric.mask(invalid)


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


def build_clean_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    edition_years = df["publishDate"].apply(parse_year)
    df["publish_year_for_disambiguation"] = pd.array([year for year, _ in edition_years], dtype="Int64")

    first_year_rows = []
    for _, row in df.iterrows():
        if normalize_date(row["firstPublishDate"]):
            year, status = parse_year(row["firstPublishDate"], row["publish_year_for_disambiguation"])
            source = "firstPublishDate"
        elif normalize_date(row["publishDate"]):
            year, status = parse_year(row["publishDate"])
            status = f"missing_firstPublishDate__{status}"
            source = "publishDate_fallback"
        else:
            year, status, source = pd.NA, "missing_both_date_fields", "missing"

        invalid_reason = ""
        clean_year = year
        if pd.isna(year):
            invalid_reason = "missing_or_unparseable_year"
        elif (
            source == "firstPublishDate"
            and status == "two_digit_year_inferred_modern"
            and int(year) >= 2022
            and pd.isna(row["publish_year_for_disambiguation"])
        ):
            clean_year = pd.NA
            invalid_reason = "ambiguous_two_digit_first_publish_year_without_publish_year"
        elif int(year) < MIN_VALID_PUBLICATION_YEAR:
            clean_year = pd.NA
            invalid_reason = "before_min_valid_publication_year"
        elif int(year) > PROJECT_END_YEAR:
            clean_year = pd.NA
            invalid_reason = "after_project_end_year"

        first_year_rows.append(
            {
                "first_publish_year": clean_year,
                "first_publish_year_source": source,
                "first_publish_year_parse_status": status,
                "first_publish_year_invalid_reason": invalid_reason,
            }
        )

    df = pd.concat([df, pd.DataFrame(first_year_rows)], axis=1)
    df["first_publish_year"] = pd.array(df["first_publish_year"], dtype="Int64")
    df = df[df["first_publish_year"].between(PROJECT_START_YEAR, PROJECT_END_YEAR)].copy()

    df["title_clean"] = df["title"].map(clean_space)
    df["title_key"] = df["title_clean"].map(make_key)

    contributors = df["author"].map(split_contributors)
    cleaned_contributors = contributors.map(lambda parts: [clean_author(part) for part in parts if clean_author(part)])
    df["author_clean"] = cleaned_contributors.map(lambda parts: ", ".join(parts))
    df["primary_author"] = cleaned_contributors.map(lambda parts: parts[0] if parts else pd.NA)
    df["author_key"] = df["primary_author"].fillna("").map(make_key)

    genres = df["genres"].map(parse_list)
    df["genres_clean"] = genres.map(lambda values: json.dumps(values, ensure_ascii=False))
    df["genres_key"] = genres.map(lambda values: json.dumps([make_key(value) for value in values], ensure_ascii=False))
    df["genre_count"] = genres.map(len).astype("Int64")
    df["primary_genre"] = genres.map(lambda values: values[0] if values else pd.NA)

    df["description_clean"] = df["description"].map(clean_description)
    df["description_word_count"] = df["description_clean"].str.findall(r"\b\w+\b").map(len).astype("Int64")

    df["averageRating"] = clean_numeric(df["rating"], min_value=0, max_value=5)
    df["numRatings_clean"] = pd.array(clean_numeric(df["numRatings"], min_value=0).round(), dtype="Int64")
    df["bbeVotes_clean"] = pd.array(clean_numeric(df["bbeVotes"], min_value=0).round(), dtype="Int64")
    df["likedPercent_clean"] = clean_numeric(df["likedPercent"], min_value=0, max_value=100)
    df["pages_clean"] = pd.array(clean_numeric(df["pages"], min_value=0).round(), dtype="Int64")

    isbn = df["isbn"].fillna("").str.strip().str.replace("-", "", regex=False).str.replace(" ", "", regex=False)
    isbn = isbn.mask(isbn.eq("9999999999999"), "")
    df["isbn_clean"] = isbn
    df["isbn_type"] = isbn.map(classify_isbn)

    df = (
        df.sort_values(["numRatings_clean", "bbeVotes_clean", "averageRating"], ascending=False)
        .drop_duplicates(["bookId"], keep="first")
        .sort_index()
        .copy()
    )

    keep = [
        "bookId",
        "title_clean",
        "title_key",
        "author_clean",
        "primary_author",
        "author_key",
        "series",
        "language",
        "first_publish_year",
        "first_publish_year_source",
        "first_publish_year_parse_status",
        "first_publish_year_invalid_reason",
        "genres_clean",
        "genres_key",
        "genre_count",
        "primary_genre",
        "description_clean",
        "description_word_count",
        "averageRating",
        "numRatings_clean",
        "bbeVotes_clean",
        "likedPercent_clean",
        "pages_clean",
        "isbn_clean",
        "isbn_type",
    ]
    return df[keep].reset_index(drop=True)


def build_summary(raw: pd.DataFrame, clean: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("raw_rows", len(raw)),
            ("clean_rows", len(clean)),
            ("rows_after_year_filter_and_bookid_dedupe", len(clean)),
            ("min_first_publish_year", clean["first_publish_year"].min()),
            ("max_first_publish_year", clean["first_publish_year"].max()),
            ("missing_bbeVotes_clean", int(clean["bbeVotes_clean"].isna().sum())),
            ("missing_description_clean", int(clean["description_clean"].str.strip().eq("").sum())),
            ("missing_genres", int(clean["genre_count"].eq(0).sum())),
        ],
        columns=["metric", "value"],
    )


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW_PATH, dtype="string", keep_default_na=False)
    clean = build_clean_dataset(raw)
    clean.to_csv(OUT_PATH, index=False)
    build_summary(raw, clean).to_csv(SUMMARY_PATH, index=False)
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
