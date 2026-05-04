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
    "romantasy",
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

KNOWN_FRANCHISE_PATTERNS = [
    r"\bharry potter\b",
    r"\bhunger games\b",
    r"\btwilight\b",
    r"\bdivergent\b",
    r"\bthe mortal instruments\b",
    r"\bthe infernal devices\b",
    r"\bpercy jackson\b",
    r"\bolympians\b",
    r"\bvampire academy\b",
    r"\bthe maze runner\b",
    r"\bthe selection\b",
    r"\bthe lunar chronicles\b",
    r"\bshadowhunters?\b",
    r"\bgrishaverse\b",
    r"\bshadow and bone\b",
    r"\bsix of crows\b",
    r"\bthrone of glass\b",
    r"\ba court of thorns and roses\b",
    r"\bacotar\b",
    r"\bshatter me\b",
    r"\bred queen\b",
    r"\bthe inheritance cycle\b",
    r"\beragon\b",
    r"\bthe chronicles of narnia\b",
    r"\bhis dark materials\b",
    r"\bartemis fowl\b",
    r"\bmiss peregrine\b",
]


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


def has_any_genre(genres: set[str], values: set[str]) -> bool:
    return bool(genres & values)


def normalize_series_text(value: object) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"#\s*[\w.\-]+(?:\s*[-&]\s*[\w.\-]+)?", " ", text)
    text = re.sub(r"\b(?:book|books|volume|vol|part)\s+\d+\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_series_metadata(value: object) -> bool:
    value = str(value or "").strip()
    return bool(value) and value.casefold() != "nan"


def has_title_series_signal(title_key: object, title_clean: object) -> bool:
    key = str(title_key or "")
    title = str(title_clean or "")
    return (
        has_text(title, r"\((?:[^)]*#\s*\d+|[^)]*\bbook\s+\d+|[^)]*\bvolume\s+\d+)[^)]*\)")
        or has_text(key, r"\b(?:trilogy|saga|chronicles|cycle|series|boxset|boxed set)\b")
        or any(has_text(key, pattern) for pattern in KNOWN_FRANCHISE_PATTERNS)
    )


def add_series_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    has_series = df["series"].map(has_series_metadata)
    inferred_series = df.apply(lambda row: has_title_series_signal(row["title_key"], row["title_clean"]), axis=1)

    series_base = df["series"].map(normalize_series_text)
    series_group_size = series_base.map(series_base[has_series].value_counts()).fillna(0).astype(int)
    ratings = pd.to_numeric(df["numRatings_clean"], errors="coerce").fillna(0)
    votes = pd.to_numeric(df["bbeVotes_clean"], errors="coerce").fillna(0)
    text_for_franchise = (
        df["title_key"].fillna("").astype(str)
        + " "
        + df["series"].fillna("").astype(str).map(normalize_series_text)
    )

    likely_blockbuster = (
        (has_series | inferred_series)
        & (
            text_for_franchise.map(lambda value: any(has_text(value, pattern) for pattern in KNOWN_FRANCHISE_PATTERNS))
            | ((series_group_size >= 3) & (ratings >= 250_000))
            | (ratings >= 1_000_000)
            | (votes >= 500)
        )
    )

    df["series_flag"] = "standalone"
    df.loc[has_series | inferred_series, "series_flag"] = "series"
    df.loc[likely_blockbuster, "series_flag"] = "blockbuster_franchise"
    return df


def assign_themes(row: pd.Series) -> dict[str, bool]:
    genres = set(parse_json_list(row["genres_key"]))
    text = f"{row['title_key']} {row['description_clean']}".casefold()

    direct_mg = bool(genres & {"middle grade", "childrens", "chapter books", "juvenile", "kids"})
    fantasy = bool(genres & {"fantasy", "magic", "urban fantasy", "epic fantasy", "high fantasy", "dragons"}) or has_text(
        text,
        r"\b(magic|magical|wizard|witch(?:es)?|dragon|dragons|prophecy|spell|spells|sorcerer|sorceress|fairy|fae|faerie)\b",
    )
    mythology = has_any_genre(genres, {"mythology", "greek mythology", "roman mythology", "norse mythology"})
    dystopian = bool(genres & {"dystopia", "dystopian", "post apocalyptic", "apocalyptic"}) or has_text(
        text,
        r"\b(dystopia|dystopian|post[- ]apocalyptic|apocalypse|rebellion|regime|districts?)\b",
    )
    romance = bool(genres & {"romance", "paranormal romance", "fantasy romance", "romantic fantasy", "new adult"}) or has_text(
        text,
        r"\b(romance|love story|fall(?:s|ing)? in love|forbidden love|mate)\b",
    )
    paranormal_genre = has_any_genre(
        genres,
        {
            "paranormal",
            "supernatural",
            "vampires",
            "werewolves",
            "shapeshifters",
            "ghosts",
            "witches",
            "angels",
            "demons",
        },
    )
    paranormal_creature_text = has_text(
        text,
        r"\b(vampires?|werewolves?|shifters?|witch(?:es)?|angels?|demons?|supernatural|paranormal)\b",
    )
    ghost_text = has_text(
        text,
        r"\b(ghosts|ghost story|ghostly|haunted house|haunted mansion|haunted by (?:a|the) ghost|spirit world|restless spirit)\b",
    )
    supernatural_elements = paranormal_genre or paranormal_creature_text or ghost_text
    real_world_genre = has_any_genre(
        genres,
        {
            "urban fantasy",
            "contemporary",
            "contemporary romance",
            "realistic fiction",
            "historical fiction",
            "mystery",
            "thriller",
            "crime",
            "ghost stories",
        },
    )
    real_world_text = has_text(
        text,
        r"\b(high school|boarding school|academy|school|new york|london|chicago|los angeles|small town|town|suburb|suburban|campus|college|family|parents?|mother|father|boyfriend|girlfriend)\b",
    )
    secondary_world_genre = has_any_genre(
        genres,
        {
            "epic fantasy",
            "high fantasy",
            "sword and sorcery",
            "fae",
            "fairies",
            "faeries",
        },
    )
    secondary_world_text = has_text(
        text,
        r"\b(kingdom|realm|empire|court|throne|crown|high fae|fae|faerie|fairy court|castle|palace|heir to the throne|royal court)\b",
    )
    real_world_adjacent = real_world_genre or real_world_text
    secondary_world = secondary_world_genre or secondary_world_text
    paranormal = supernatural_elements and real_world_adjacent and not secondary_world and not mythology
    fantasy_worldbuilding = secondary_world or has_text(
        text,
        r"\b(magic|magical|kingdom|realm|empire|court|throne|crown|castle|palace|dragon|dragons|sword|warrior|assassin|heir|quest|prophecy)\b",
    )
    romance_genre = has_any_genre(
        genres,
        {"romance", "fantasy romance", "romantic fantasy", "new adult"},
    )
    romance_forward_text = has_text(
        text,
        r"\b(lovers?|enemies to lovers|love triangle|romantic|romance|forbidden love|fall(?:s|ing)? in love|mate|desire|passion|seductive)\b",
    )
    heavy_romance = romance_genre or romance_forward_text

    flags = {
        "theme_middle_grade_fantasy": direct_mg and fantasy,
        "theme_mythology_adventure": mythology
        or (
            "adventure" in genres
            and has_text(text, r"\b(mythology|goddess|demigod|olympian|greek|roman|norse|egyptian)\b")
        ),
        "theme_paranormal_supernatural": paranormal,
        "theme_paranormal_romance": paranormal and romance,
        "theme_dystopian_post_apocalyptic": dystopian,
        "theme_epic_high_fantasy": bool(genres & {"epic fantasy", "high fantasy", "dragons", "sword and sorcery"})
        or (
            secondary_world
            and not real_world_adjacent
            and not dystopian
            and not bool(genres & {"science fiction", "sci fi", "space", "space opera", "cyberpunk"})
        )
        or (
            "fantasy" in genres
            and not dystopian
            and not bool(genres & {"science fiction", "sci fi", "space", "space opera", "cyberpunk"})
            and has_text(text, r"\b(kingdom|realm|empire|throne|crown|dragon|dragons|sword|warrior)\b")
        ),
        "theme_romantasy": (
            fantasy
            and heavy_romance
            and fantasy_worldbuilding
            and not real_world_adjacent
            and not dystopian
            and not bool(genres & {"science fiction", "sci fi", "space", "space opera", "cyberpunk"})
        ),
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
    nonfiction = bool(
        genres
        & {
            "nonfiction",
            "biography",
            "memoir",
            "history",
            "politics",
            "business",
            "finance",
            "self help",
            "travel",
            "religion",
            "science",
        }
    )
    fiction_or_speculative = bool(
        genres
        & {
            "fiction",
            "fantasy",
            "science fiction",
            "dystopia",
            "dystopian",
            "post apocalyptic",
            "apocalyptic",
            "paranormal",
            "supernatural",
            "urban fantasy",
            "young adult fantasy",
            "middle grade",
            "childrens",
        }
    )
    school_age = has_text(
        text,
        r"\b(teen(?:age|ager|agers)?|high school|boarding school|sixteen[- ]year[- ]old|seventeen[- ]year[- ]old|eighteen[- ]year[- ]old|fifteen[- ]year[- ]old|fourteen[- ]year[- ]old|thirteen[- ]year[- ]old|coming[- ]of[- ]age)\b",
    )
    child_age = has_text(text, r"\b(twelve[- ]year[- ]old|eleven[- ]year[- ]old|ten[- ]year[- ]old|middle school|children's|childrens|kids)\b")
    known_ya = author_key in KNOWN_YA_AUTHORS
    known_mg = author_key in KNOWN_MG_AUTHORS
    known_crossover = title_key in KNOWN_CROSSOVER_TITLES
    adult_exclusion = bool(genres & {"erotica", "bdsm", "business", "finance", "self help", "adult", "adult fiction"})

    has_theme = bool(theme_tags)
    if nonfiction and not fiction_or_speculative:
        return False, "out_of_scope", "exclude_nonfiction"

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

    df = df[df["is_youth_scope"] & df["theme_count"].gt(0)].reset_index(drop=True)
    return add_series_flag(df)


def build_summary(clean: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("clean_rows", len(clean)),
        ("scope_rows", len(scope)),
    ]
    rows.extend((f"audience_{key}", int(value)) for key, value in scope["audience"].value_counts().items())
    rows.extend((f"series_flag_{key}", int(value)) for key, value in scope["series_flag"].value_counts().items())
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
