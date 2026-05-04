# Methodology

This study examines how dominant themes in culturally visible youth fiction changed between 1997 and 2024. The analysis uses Goodreads' "Best Books Ever" dataset as a proxy for reader-recognized books rather than for the full publishing market. Because the dataset reflects books that accumulated ratings, votes, and long-term visibility on Goodreads, the findings should be interpreted as patterns in collective reader memory, not as a complete record of all books published during the period.

## Data Source

The source dataset is the Goodreads "Best Books Ever" Kaggle dataset: <https://www.kaggle.com/datasets/pooriamst/best-books-ever-dataset>. For local reproduction, the downloaded CSV is stored as `data/raw/books_goodreads.csv`. It contains 52,478 Goodreads records with bibliographic metadata, publication dates, genre labels, descriptions, ratings, rating counts, and Goodreads "Best Books Ever" voting fields.

The raw data includes inconsistent date formats, duplicated book identifiers, uneven genre labeling, missing descriptions, and numeric fields stored as text. These issues were addressed before the analytical sample was constructed.

## Sample Construction

The final sample was built in three stages.

First, the raw file was cleaned and restricted to books with a valid first publication year between 1997 and 2024. The date-cleaning procedure used `firstPublishDate` when available and used `publishDate` only as a fallback when the first publication date was missing. Mixed date formats were parsed into a single `first_publish_year` field. Values outside the project range were excluded from the cleaned dataset. Ambiguous two-digit `firstPublishDate` values that would otherwise create unverified 2022+ publication years were excluded unless a usable edition-year signal supported the interpretation. Duplicate rows with the same `bookId` were collapsed by retaining the row with the highest number of ratings, then highest Goodreads vote count, then highest average rating. This produced `data/clean_books.csv` with 37,281 records.

Second, the cleaned records were filtered to the project's substantive scope: youth fiction associated with fantasy, speculative fiction, or adjacent genre trends. A book was included if it had a youth-audience signal and at least one project theme. Youth-audience signals came from genre labels, title and description text, and a small set of known author or title checks for edge cases. Included books were assigned to one audience category: `middle_grade`, `young_adult`, or `crossover`. Crossover books are titles that are not always explicitly labeled as YA or middle grade but are widely associated with youth readership or coming-of-age reading cultures. This produced `data/scope_books.csv` with 6,552 records.

Third, a weighted popularity score was calculated for the scoped books. The resulting file, `data/processed_books.csv`, is the main analysis dataset.

## Cleaning Procedures

Text fields were normalized to reduce formatting noise. Titles, authors, genres, and descriptions were stripped of control characters and repeated whitespace. Author names were cleaned to remove role annotations, and a primary-author key was created for matching. Genre lists were parsed from their raw string representation into cleaned JSON-style lists and normalized keys.

Numeric fields were converted from text into usable numeric columns. The analysis uses `averageRating`, `numRatings_clean`, and `bbeVotes_clean`. The raw `bbeScore` field was not used as an analytical variable because it is a platform-specific aggregate whose construction is less transparent than ratings, average rating, and vote count.

## Audience and Theme Classification

The project uses rule-based classification rather than machine learning. This choice keeps the inclusion logic interpretable and easier to audit.

The taxonomy below is the locked version used for the final era charts and exported analytical tables.

Each scoped book was assigned one audience label:

- `middle_grade`
- `young_adult`
- `crossover`

Books were then tagged with one or more theme buckets:

- `middle_grade_fantasy`
- `mythology_adventure`
- `paranormal_supernatural`
- `paranormal_romance`
- `dystopian_post_apocalyptic`
- `epic_high_fantasy`
- `romantasy`
- `science_fiction`

Theme assignment used Goodreads genre labels together with keyword evidence from titles and descriptions. Dystopian and post-apocalyptic books were identified through genre labels such as `dystopia` and through text patterns such as "rebellion", "regime", "district", or "apocalypse". Paranormal and supernatural books were defined as books with supernatural beings or forces in a real-world-adjacent setting, using signals such as `urban fantasy`, `paranormal`, `supernatural`, vampires, werewolves, ghosts, angels, or demons together with school, city, town, or family-life cues. Epic or high fantasy was defined as fantasy in a secondary-world setting, using genre labels such as `high fantasy` or `epic fantasy` and worldbuilding terms such as "kingdom", "realm", "court", "throne", or "crown". This setting distinction was used to keep secondary-world fantasy romance titles separate from the paranormal wave. Singular metaphorical uses such as "ghost haunting him" were not treated as sufficient evidence on their own. Romantasy was defined more narrowly as romance-forward fantasy in a non-real-world fantasy frame, using strong romance signals together with fantasy-world or magical-worldbuilding cues while excluding dystopian, science-fiction, and real-world paranormal settings.

The scoped dataset contains:

- 3,963 young adult books
- 2,317 middle grade books
- 272 crossover books

Nonfiction records without a fiction or speculative genre signal were excluded from the youth-fiction scope, even when their descriptions contained dystopian-adjacent language.

Because a book can belong to multiple themes, theme counts are not mutually exclusive.

## Popularity Score

Popularity was operationalized as a composite measure of visibility, reader affection, and Goodreads canonization. The score combines three standardized components:

- `log1p(numRatings_clean)`, representing reader visibility
- `averageRating`, representing reader affection
- `log1p(bbeVotes_clean)`, representing recognition within the Goodreads "Best Books Ever" voting context

The score is calculated as:

$$
popularity\_score =
0.5 * z(log1p(numRatings\_clean))
+ 0.3 * z(averageRating)
+ 0.2 * z(log1p(bbeVotes\_clean))
$$

Rating counts and vote counts were log-transformed to reduce the dominance of extreme blockbuster titles while preserving their relative importance. Each component was standardized before weighting. The largest weight was assigned to rating count because broad reader visibility is central to this project's definition of cultural memory. Average rating received a smaller but meaningful weight because highly rated books may be culturally important even when their audience is smaller. Goodreads vote count received the lowest weight because it is useful evidence of canonization but is more tightly tied to the specific platform list.

## Analytical Dataset

The main dataset for analysis is `data/processed_books.csv`. It contains the cleaned bibliographic fields, first publication year, audience category, theme indicators, `series_flag`, popularity score components, final `popularity_score`, and `popularity_rank`.

Because the available scoped records effectively end in 2021 after cleaning and filtering, the final era analysis charts use 1997-2021 as the realized analytical time span even though the project frame remains 1997-2024.

The unit of analysis is the individual book, not the series. This preserves the ability to study blockbuster effects, since major series can influence theme trends through multiple highly visible entries.

## Limitations

The dataset is not representative of all youth fiction published between 1997 and 2024. It overrepresents books that remained visible on Goodreads and underrepresents obscure, recently published, non-English, or less frequently rated titles. The rule-based theme system is transparent but imperfect; some books may be misclassified when metadata is sparse, genre labels are inconsistent, or descriptions emphasize only part of the book's content. For these reasons, results should be interpreted as evidence of dominant patterns in Goodreads-canonized youth fiction rather than as definitive claims about the entire publishing field.

## Reproducibility

The full processing pipeline is implemented in three scripts:

```bash
.venv/bin/python scripts/01_clean_books.py
.venv/bin/python scripts/02_scope_books.py
.venv/bin/python scripts/03_score_books.py
.venv/bin/python scripts/04_export_theme_era_outputs.py
.venv/bin/python scripts/05_exploratory_analysis.py
```

The raw Kaggle CSV and generated book-level datasets are local artifacts and are not committed to GitHub. Compact pipeline summaries are stored in `data/reference/`. Era-analysis tables and charts are exported to `outputs/tables/` and `outputs/charts/`. Rough story-finding tables and sanity-check charts are exported to `outputs/exploratory/`.
