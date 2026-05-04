# Data

This folder is intentionally compact.

## Datasets

```text
data/
├── raw/
│   └── books_goodreads.csv      # local only, downloaded from Kaggle
├── clean_books.csv              # local generated artifact
├── scope_books.csv              # local generated artifact
├── processed_books.csv          # local generated artifact
└── reference/
    ├── cleaning_summary.csv
    ├── scope_summary.csv
    └── popularity_score_summary.csv
```

## Dataset Roles

- `raw/books_goodreads.csv`: original Kaggle Goodreads source file, downloaded locally from <https://www.kaggle.com/datasets/pooriamst/best-books-ever-dataset>.
- `clean_books.csv`: cleaned, date-filtered, deduped books from 1997-2024.
- `scope_books.csv`: youth fantasy scoped books with audience and theme labels.
- `processed_books.csv`: final analysis dataset with `popularity_score` and `series_flag`.
- `reference/`: compact run summaries for the cleaning, scoping, and scoring stages.

Final analysis tables and charts are written to `outputs/`, not `data/`.

## Regenerate Data

Download the Kaggle dataset and place the source CSV at:

```text
data/raw/books_goodreads.csv
```

Then run the pipeline:

```bash
.venv/bin/python scripts/01_clean_books.py
.venv/bin/python scripts/02_scope_books.py
.venv/bin/python scripts/03_score_books.py
```

Optional era-analysis exports:

```bash
.venv/bin/python scripts/04_export_theme_era_outputs.py
.venv/bin/python scripts/05_exploratory_analysis.py
```

## Notes

- Raw and generated dataset CSV files are intentionally not committed to GitHub.
- `bbeScore` is retained only in the raw source and is not used for analysis.
- The final dataset for analysis is `data/processed_books.csv`.
