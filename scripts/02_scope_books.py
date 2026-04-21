from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "clean_books.csv"
OUT_PATH = ROOT / "data" / "scope_books.csv"
SUMMARY_PATH = ROOT / "data" / "reference" / "scope_summary.csv"

THEMES = [
    "middle_grade_fantasy",
    "mythology_adventure",
    "paranormal_supernatural",
    "paranormal_romance",
    "dystopian_post_apocalyptic",
    "epic_high_fantasy",
    "romantasy_fae",
    "science_fiction",
]

KNOWN_YA_AUTHORS = {
    "suzanne collins",
    "stephenie meyer",
    "john green",
    "veronica roth",
    "cassandra clare",
    "sarah j maas",
    "leigh bardugo",
    "marie lu",
    "rainbow rowell",
    "holly black",
    "maggie stiefvater",
    "jenny han",
    "tahereh mafi",
    "sabaa tahir",
    "marissa meyer",
    "kiera cass",
    "richelle mead",
    "lauren oliver",
    "patrick ness",
    "scott westerfeld",
    "james dashner",
}

KNOWN_MG_AUTHORS = {
    "j k rowling",
    "rick riordan",
    "c s lewis",
    "lemony snicket",
    "roald dahl",
    "louis sachar",
    "eoin colfer",
    "kate dicamillo",
    "jeff kinney",
    "r j palacio",
}

KNOWN_CROSSOVER_TITLES = {
    "the book thief",
    "the giver",
    "the outsiders",
    "the perks of being a wallflower",
    "a wrinkle in time",
    "holes",
    "anne of green gables",
    "little women",
    "the chronicles of narnia",
    "his dark materials",
    "the golden compass",
    "the graveyard book",
    "coraline",
}


def parse_json_list(value: object) -> list[str]:
    if pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def has_text(value: object, pattern: str) -> bool:
    return re.search(pattern, str(value or ""), flags=re.IGNORECASE) is not None


def assign_themes(row: pd.Series) -> dict[str, bool]:
    genres = set(parse_json_list(row["genres_key"]))
    text = f"{row['title_key']} {row['description_clean']}".casefold()

    direct_mg = bool(genres & {"middle grade", "childrens", "chapter books", "juvenile", "kids"})
    fantasy = bool(genres & {"fantasy", "magic", "urban fantasy", "epic fantasy", "high fantasy", "dragons"}) or has_text(
        text,
        r"\b(magic|wizard|witch|dragon|kingdom|curse|prophecy|quest)\b",
    )
    romance = bool(genres & {"romance", "paranormal romance", "fantasy romance", "romantic fantasy", "new adult"}) or has_text(
        text,
        r"\b(romance|love story|fall(?:s|ing)? in love|forbidden love|mate)\b",
    )
    paranormal = bool(
        genres
        & {
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
    ) or has_text(text, r"\b(vampire|werewolf|shifter|ghost|witch|angel|demon|supernatural|paranormal)\b")

    flags = {
        "theme_middle_grade_fantasy": direct_mg and fantasy,
        "theme_mythology_adventure": bool(genres & {"mythology", "adventure"})
        and has_text(text, r"\b(mythology|gods?|goddess|demigod|olympian|greek|roman|norse|egyptian|quest|prophecy)\b"),
        "theme_paranormal_supernatural": paranormal,
        "theme_paranormal_romance": paranormal and romance,
        "theme_dystopian_post_apocalyptic": bool(genres & {"dystopia", "dystopian", "post apocalyptic", "apocalyptic"})
        or has_text(text, r"\b(dystopia|dystopian|post[- ]apocalyptic|apocalypse|rebellion|regime|districts?)\b"),
        "theme_epic_high_fantasy": bool(genres & {"epic fantasy", "high fantasy", "dragons", "sword and sorcery"})
        or ("fantasy" in genres and has_text(text, r"\b(kingdom|realm|empire|throne|crown|dragon|quest|prophecy|sword|warrior|magic)\b")),
        "theme_romantasy_fae": fantasy
        and romance
        and has_text(text, r"\b(fae|faerie|fairy|faeries|court|curse|shadow|kingdom|prince|princess)\b"),
        "theme_science_fiction": bool(genres & {"science fiction", "sci fi", "space", "space opera", "time travel", "cyberpunk", "aliens"})
        or has_text(text, r"\b(science fiction|sci[- ]fi|space|alien|spaceship|time travel|cyberpunk|android|robot)\b"),
    }
    return flags


def assign_audience(row: pd.Series, theme_tags: list[str]) -> tuple[bool, str, str]:
    genres = set(parse_json_list(row["genres_key"]))
    title_key = str(row["title_key"])
    author_key = str(row["author_key"])
    text = f"{row['title_key']} {row['description_clean']}".casefold()

    direct_ya = bool(genres & {"young adult", "teen", "ya"})
    direct_mg = bool(genres & {"middle grade", "childrens", "chapter books", "juvenile", "kids"})
    school_age = has_text(
        text,
        r"\b(teen(?:age|ager|agers)?|high school|boarding school|academy|sixteen[- ]year[- ]old|seventeen[- ]year[- ]old|eighteen[- ]year[- ]old|fifteen[- ]year[- ]old|fourteen[- ]year[- ]old|thirteen[- ]year[- ]old|coming[- ]of[- ]age)\b",
    )
    child_age = has_text(text, r"\b(twelve[- ]year[- ]old|eleven[- ]year[- ]old|ten[- ]year[- ]old|middle school|children's|childrens|kids)\b")
    known_ya = author_key in KNOWN_YA_AUTHORS
    known_mg = author_key in KNOWN_MG_AUTHORS
    known_crossover = title_key in KNOWN_CROSSOVER_TITLES
    adult_exclusion = bool(genres & {"erotica", "bdsm", "business", "finance", "self help", "adult", "adult fiction"})

    has_theme = bool(theme_tags)
    direct_or_known = direct_ya or direct_mg or known_ya or known_mg or known_crossover
    inferred = has_theme and (school_age or child_age)
    included = direct_or_known or inferred
    if adult_exclusion and not direct_or_known:
        included = False

    if not included:
        return False, "out_of_scope", "exclude_no_strong_youth_signal"
    if known_crossover and not (direct_mg or known_mg or child_age):
        return True, "crossover", "include_crossover"
    if inferred and not direct_or_known:
        return True, "crossover", "include_crossover"
    if direct_mg or known_mg or child_age:
        return True, "middle_grade", "include_middle_grade"
    return True, "young_adult", "include_young_adult"


def build_scope(clean: pd.DataFrame) -> pd.DataFrame:
    df = clean.copy()
    theme_flags = pd.DataFrame(df.apply(assign_themes, axis=1).tolist(), index=df.index)
    df = pd.concat([df, theme_flags], axis=1)
    df["theme_tags"] = df.apply(
        lambda row: json.dumps([theme for theme in THEMES if bool(row[f"theme_{theme}"])], ensure_ascii=False),
        axis=1,
    )
    df["theme_count"] = df["theme_tags"].map(lambda value: len(parse_json_list(value))).astype("Int64")

    audience = df.apply(lambda row: assign_audience(row, parse_json_list(row["theme_tags"])), axis=1)
    df["is_youth_scope"] = [item[0] for item in audience]
    df["audience"] = [item[1] for item in audience]
    df["audience_rule"] = [item[2] for item in audience]

    return df[df["is_youth_scope"] & df["theme_count"].gt(0)].reset_index(drop=True)


def build_summary(clean: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("clean_rows", len(clean)),
        ("scope_rows", len(scope)),
    ]
    rows.extend((f"audience_{key}", int(value)) for key, value in scope["audience"].value_counts().items())
    for theme in THEMES:
        rows.append((theme, int(scope[f"theme_{theme}"].sum())))
    return pd.DataFrame(rows, columns=["metric", "value"])


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean = pd.read_csv(INPUT_PATH, low_memory=False)
    scope = build_scope(clean)
    scope.to_csv(OUT_PATH, index=False)
    build_summary(clean, scope).to_csv(SUMMARY_PATH, index=False)
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
