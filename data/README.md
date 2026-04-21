# Data

This folder is intentionally compact.

## Datasets

```text
data/
├── raw/
│   └── books_goodreads.csv
├── clean_books.csv
├── scope_books.csv
├── processed_books.csv
└── reference/
    ├── cleaning_summary.csv
    ├── scope_summary.csv
    └── popularity_score_summary.csv
```

## Dataset Roles

- `raw/books_goodreads.csv`: original Kaggle Goodreads source file.
- `clean_books.csv`: cleaned, date-filtered, deduped books from 1997-2024.
- `scope_books.csv`: youth fantasy scoped books with audience and theme labels.
- `processed_books.csv`: final analysis dataset with `popularity_score`.

## Regenerate Data

Run all three steps:

```bash
.venv/bin/python scripts/01_clean_books.py
.venv/bin/python scripts/02_scope_books.py
.venv/bin/python scripts/03_score_books.py
```

## Notes

- Generated CSV files are local analysis artifacts.
- `bbeScore` is retained only in the raw source and is not used for analysis.
- The final dataset for analysis is `data/processed_books.csv`.
