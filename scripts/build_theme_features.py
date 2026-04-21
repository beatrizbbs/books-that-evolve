from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
BRIDGE_DIR = PROCESSED_DIR / "bridge"
REFERENCE_DIR = PROCESSED_DIR / "reference"
INPUT_PATH = ANALYSIS_DIR / "books_analysis.csv"
THEMED_BOOKS_PATH = ANALYSIS_DIR / "books_themed.csv"
BOOK_THEMES_PATH = BRIDGE_DIR / "book_themes.csv"
THEME_SUMMARY_PATH = REFERENCE_DIR / "theme_summary.csv"


THEME_COLUMNS = [
    "theme_middle_grade_fantasy",
    "theme_mythology_adventure",
    "theme_paranormal_supernatural",
    "theme_paranormal_romance",
    "theme_dystopian_post_apocalyptic",
    "theme_epic_high_fantasy",
    "theme_romantasy_fae",
    "theme_contemporary_realistic",
    "theme_science_fiction",
    "theme_horror_dark",
    "theme_graphic_manga_comics",
]


def parse_json_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def make_search_text(row: pd.Series) -> str:
    parts = [
        row.get("title_clean", ""),
        row.get("description_clean", ""),
    ]
    return " ".join(str(part).casefold() for part in parts if pd.notna(part))


def has_any(value_set: set[str], terms: set[str]) -> bool:
    return bool(value_set & terms)


def text_has(search_text: str, pattern: str) -> bool:
    return re.search(pattern, search_text, flags=re.IGNORECASE) is not None


def assign_theme_flags(row: pd.Series) -> dict[str, bool]:
    genre_keys = set(parse_json_list(row.get("genres_key", "[]")))
    search_text = make_search_text(row)

    middle_grade_youth = {"middle grade", "childrens"}
    fantasy = {
        "fantasy",
        "magic",
        "urban fantasy",
        "epic fantasy",
        "high fantasy",
        "dragons",
        "sword and sorcery",
    }
    romance = {
        "romance",
        "paranormal romance",
        "contemporary romance",
        "fantasy romance",
        "romantic fantasy",
        "historical romance",
        "new adult",
    }
    paranormal = {
        "paranormal",
        "supernatural",
        "vampires",
        "werewolves",
        "shapeshifters",
        "ghosts",
        "witches",
        "angels",
        "demons",
        "urban fantasy",
    }
    dystopian = {
        "dystopia",
        "dystopian",
        "post apocalyptic",
        "apocalyptic",
    }
    contemporary = {
        "contemporary",
        "realistic fiction",
        "young adult contemporary",
        "teen",
        "school",
        "coming of age",
        "chick lit",
        "new adult",
    }
    sci_fi = {
        "science fiction",
        "sci fi",
        "space",
        "space opera",
        "time travel",
        "cyberpunk",
        "aliens",
        "dystopia",
    }
    horror_genres = {
        "horror",
        "gothic",
        "ghosts",
        "monsters",
        "zombies",
        "dark fantasy",
    }
    graphic = {
        "manga",
        "graphic novels",
        "graphic novels comics",
        "comics",
        "comic book",
        "sequential art",
        "manhwa",
    }

    has_middle_grade_youth = has_any(genre_keys, middle_grade_youth)
    has_fantasy = has_any(genre_keys, fantasy) or text_has(
        search_text,
        r"\b(magic|wizard|witch|dragon|kingdom|curse|prophecy|quest)\b",
    )
    has_romance = has_any(genre_keys, romance) or text_has(
        search_text,
        r"\b(romance|love story|fall(?:s|ing)? in love|forbidden love|mate)\b",
    )
    has_paranormal = has_any(genre_keys, paranormal) or text_has(
        search_text,
        r"\b(vampire|werewolf|shifter|ghost|witch|angel|demon|supernatural|paranormal)\b",
    )

    flags = {
        "theme_middle_grade_fantasy": (
            has_middle_grade_youth
            and has_fantasy
        ),
        "theme_mythology_adventure": has_any(genre_keys, {"mythology", "adventure"})
        and text_has(
            search_text,
            r"\b(mythology|gods?|goddess|demigod|olympian|greek|roman|norse|egyptian|quest|prophecy)\b",
        ),
        "theme_paranormal_supernatural": has_paranormal,
        "theme_paranormal_romance": has_paranormal and has_romance,
        "theme_dystopian_post_apocalyptic": has_any(genre_keys, dystopian)
        or text_has(
            search_text,
            r"\b(dystopia|dystopian|post[- ]apocalyptic|apocalypse|rebellion|regime|districts?)\b",
        ),
        "theme_epic_high_fantasy": has_any(
            genre_keys,
            {"epic fantasy", "high fantasy", "dragons", "sword and sorcery"},
        )
        or (
            "fantasy" in genre_keys
            and text_has(
                search_text,
                r"\b(kingdom|realm|empire|throne|crown|dragon|quest|prophecy|sword|warrior|magic)\b",
            )
        ),
        "theme_romantasy_fae": has_fantasy
        and has_romance
        and text_has(
            search_text,
            r"\b(fae|faerie|fairy|faeries|court|curse|shadow|kingdom|prince|princess)\b",
        ),
        "theme_contemporary_realistic": has_any(genre_keys, contemporary)
        and not has_fantasy
        and not has_paranormal,
        "theme_science_fiction": has_any(genre_keys, sci_fi)
        or text_has(
            search_text,
            r"\b(science fiction|sci[- ]fi|space|alien|spaceship|time travel|cyberpunk|android|robot)\b",
        ),
        "theme_horror_dark": has_any(genre_keys, horror_genres)
        or text_has(
            search_text,
            r"\b(horror|haunted|ghost|zombie|killer|murder|dark secret|nightmare)\b",
        ),
        "theme_graphic_manga_comics": has_any(genre_keys, graphic),
    }
    return flags


def add_theme_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    theme_flags = pd.DataFrame(df.apply(assign_theme_flags, axis=1).tolist(), index=df.index)

    for column in THEME_COLUMNS:
        df[column] = theme_flags[column].fillna(False)

    def theme_tags(row: pd.Series) -> list[str]:
        return [column.replace("theme_", "") for column in THEME_COLUMNS if bool(row[column])]

    tags = df.apply(theme_tags, axis=1)
    df["theme_tags"] = tags.map(lambda values: json.dumps(values, ensure_ascii=False))
    df["theme_count"] = tags.map(len).astype("Int64")
    df["has_theme"] = df["theme_count"].gt(0)
    return df


def build_theme_membership(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        tags = parse_json_list(row["theme_tags"])
        if not tags:
            continue
        weight = 1 / len(tags)
        for theme in tags:
            rows.append(
                {
                    "bookId": row["bookId"],
                    "title_clean": row["title_clean"],
                    "primary_author": row["primary_author"],
                    "first_publish_year": row["first_publish_year"],
                    "theme": theme,
                    "theme_weight": weight,
                    "numRatings_clean": row["numRatings_clean"],
                    "averageRating": row["averageRating"],
                    "bbeVotes_clean": row["bbeVotes_clean"],
                }
            )
    return pd.DataFrame(rows)


def build_theme_summary(df: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    counts = (
        membership.groupby("theme", dropna=False)
        .agg(
            book_count=("bookId", "count"),
            weighted_book_count=("theme_weight", "sum"),
            median_first_publish_year=("first_publish_year", "median"),
            total_num_ratings=("numRatings_clean", "sum"),
            median_average_rating=("averageRating", "median"),
        )
        .reset_index()
        .sort_values(["book_count", "theme"], ascending=[False, True])
    )
    total = pd.DataFrame(
        [
            {
                "theme": "_all_books",
                "book_count": len(df),
                "weighted_book_count": len(df),
                "median_first_publish_year": df["first_publish_year"].median(),
                "total_num_ratings": df["numRatings_clean"].sum(),
                "median_average_rating": df["averageRating"].median(),
            },
            {
                "theme": "_untagged_books",
                "book_count": int((~df["has_theme"]).sum()),
                "weighted_book_count": int((~df["has_theme"]).sum()),
                "median_first_publish_year": df.loc[~df["has_theme"], "first_publish_year"].median(),
                "total_num_ratings": df.loc[~df["has_theme"], "numRatings_clean"].sum(),
                "median_average_rating": df.loc[~df["has_theme"], "averageRating"].median(),
            },
        ]
    )
    return pd.concat([total, counts], ignore_index=True)


def main() -> None:
    for directory in [ANALYSIS_DIR, BRIDGE_DIR, REFERENCE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    books = pd.read_csv(INPUT_PATH, low_memory=False)
    books_themed = add_theme_columns(books)
    theme_membership = build_theme_membership(books_themed)
    theme_summary = build_theme_summary(books_themed, theme_membership)

    books_themed.to_csv(THEMED_BOOKS_PATH, index=False)
    theme_membership.to_csv(BOOK_THEMES_PATH, index=False)
    theme_summary.to_csv(THEME_SUMMARY_PATH, index=False)

    print(f"Wrote {THEMED_BOOKS_PATH.relative_to(ROOT)}")
    print(f"Wrote {BOOK_THEMES_PATH.relative_to(ROOT)}")
    print(f"Wrote {THEME_SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
