<h1 align="center">
  <br>
  <a href="assets/logo.png"><img src="assets/logo.png" alt="Books That Evolve Logo" width="200"></a>
  <br>
  Books That Evolve: <br> A Cultural Memory Analysis of Modern Reading Eras
  <br>
</h1>

<h4 align="center">A cultural memory analysis of modern reading eras through Goodreads-canonized youth fiction during 1997–2024.</h4>
<p align="center">
  <img src="https://img.shields.io/badge/Python-c59a6d?style=for-the-badge&logo=python&logoColor=white" alt="Python" height="15"/>
  <img src="https://img.shields.io/badge/Pandas-996b53?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" height="15"/>
  <img src="https://img.shields.io/badge/NumPy-a86060?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy" height="15"/>
  <img src="https://img.shields.io/badge/Matplotlib-9e9268?style=for-the-badge&logo=plotly&logoColor=white" alt="Matplotlib" height="15"/>
  <img src="https://img.shields.io/badge/Jupyter-ac8862?style=for-the-badge&logo=jupyter&logoColor=white" alt="Jupyter" height="15"/>
  <img src="https://img.shields.io/badge/Tableau-866031?style=for-the-badge&logo=tableau&logoColor=white" alt="Tableau" height="15"/>
</p>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#project-goal">Project Goal</a> •
  <a href="#dataset">Dataset</a> •
  <a href="#scope">Scope</a> •
  <a href="#method">Method</a> •
  <a href="#results">Analysis</a> •
  <a href="#results">Results</a> •
  <a href="#visualizations">Visualizations</a>  •
  <a href="#repo-structure">Repo Structure</a> •
  <a href="#how-to-run">How to Run</a>
</p>

## Overview

This project explores how **beloved youth-fiction books**—particularly those that remained highly visible on Goodreads—reflect shifting cultural trends from the late 1990s through the 2020s.

Rather than analyzing the full publishing market, this project focuses on **books that endured**: titles that accumulated long-term reader attention, affection, and recognition. These books form a kind of **collective reading memory**, capturing not just what was published, but what *stuck*.

The goal is to trace how dominant themes evolved across modern reading eras—from middle grade fantasy and mythology-driven adventures to paranormal romance, dystopian fiction, and later forms of fantasy.

---

## Project Goal

### Primary Question

* **How did the dominant themes in beloved youth-fiction books change from 1997 to 2024?**

### Secondary Questions

* Which genres or themes defined different reading eras?
* Were perceived trends driven by broad movements or a few blockbuster series?
* How did the *anguage of book titles and descriptions evolve over time?

---

## Dataset

This project uses the **Goodreads “Best Books Ever” dataset** from Kaggle (~52,000 books, 25+ features).

### Key Fields

* `title`
* `author`
* `firstPublishDate`
* `genres`
* `description`
* `numRatings`
* `averageRating`
* `bbeVotes`, `bbeScore`

### Why This Dataset?

Unlike a full publishing catalog, this dataset reflects:

* Long-term reader engagement
* Cultural visibility
* Canonized books that remain widely discussed

It is therefore well-suited for analyzing **cultural memory rather than market output**.

### Limitations

* Not a complete sample of all published books
* Skewed toward popular and highly rated titles
* Overrepresents blockbuster series and enduring favorites
* Missing or inconsistent metadata in some fields
* Reflects Goodreads user behavior (platform bias)

---

## Scope

### Time Range

1997–2024

### Included Books

* Young Adult (YA)
* Middle Grade (MG)
* Crossover titles

**Crossover books** are defined as titles not always explicitly shelved as YA or MG, but widely read or culturally associated with youth audiences.

### Unit of Analysis

* Individual books (not series as a single unit)
* Grouped by **first publication year**

### Series Handling

* Books analyzed individually
* Series membership flagged to study **blockbuster effects**

### Thematic Focus

The project considers youth fiction broadly, with emphasis on:

* Middle grade fantasy
* Mythology / adventure
* Paranormal / supernatural
* Dystopian fiction
* Epic / high fantasy
* Romantasy-adjacent trends

---

## Method

### 1. Data Cleaning

* Standardized publication dates
* Cleaned genres and descriptions
* Removed duplicates and invalid records

### 2. Feature Engineering

#### Time Features

* Extracted `first_publish_year`
* Created era groupings:

  * 1997–2004
  * 2005–2012
  * 2013–2018
  * 2019–2024

#### Theme Buckets

Custom categories created using keyword-based tagging from:

* Genres
* Titles
* Descriptions

Examples:

* Middle Grade Fantasy
* Paranormal Romance
* Dystopian
* Epic / High Fantasy
* Fae / Romantasy

#### Popularity Score

A composite score capturing cultural impact:

$$
\text{Popularity Score} =
0.5 \cdot z(\log(1 + \text{numRatings})) +
0.3 \cdot z(\text{averageRating}) +
0.2 \cdot z(\log(1 + \text{bbeVotes}))
$$

This integrates:

* **Visibility** (ratings count)
* **Affection** (average rating)
* **Canonization** (Goodreads voting)

---

## Analysis

The analysis focuses on:

### Theme Trends Over Time

* Share of popularity by theme across years
* Identification of dominant genres in each era

### Era-Defining Books

* Top books by popularity score within each period
* Identification of key authors and series

### Keyword Evolution

Tracking changes in language across decades:

* “vampire”, “academy”, “dystopia”
* “kingdom”, “fae”, “court”, “shadow”

### Blockbuster Effect

* Comparing trends with and without top-performing books
* Measuring influence of major series

---

## Results

Key findings include:

* Clear **genre waves** across modern youth fiction
* Evidence that a small number of blockbuster series strongly shaped perceived trends
* Evolution not just in genre, but in **tone and vocabulary**

---

## Visualizations

The project includes:

* Theme dominance over time
* Era-based genre comparisons
* Top books per era
* Keyword trend charts

(*Dashboard version planned in future work*)

---

## Repo Structure

```bash
books-that-evolve/
│
├── data/               # Raw and cleaned datasets
├── notebooks/          # Cleaning, EDA, feature engineering
├── outputs/            # Final charts and tables
├── assets/             # Images / visuals
├── README.md
└── requirements.txt
```

---

## How to Run

```bash
git clone https://github.com/beatrizbbs/books-that-evolve.git
cd books-that-evolve
pip install -r requirements.txt
```

Open notebooks in Jupyter:

```bash
jupyter notebook
```

---

## Next Steps

* Improve genre classification using NLP or embeddings
* Add topic modeling for deeper theme discovery
* Integrate additional datasets (Open Library, Google Books)
* Build interactive dashboard (Streamlit or Tableau)
* Refine blockbuster/series analysis

---

## Project Framing

This is not a traditional market analysis.

It is a **cultural reading-history project**—an exploration of how readers collectively remember and define literary eras through the books that endured.

---

## Inspiration

This project was inspired by personal observations of shifting reading trends—from the dominance of middle grade fantasy to paranormal romance, dystopian fiction, and evolving fantasy subgenres—and the question of whether these perceived “eras” are reflected in data.

---

## License

This project is released under the MIT License.

---

## Final Note

This project combines:

* Data cleaning
* Feature engineering
* Text analysis
* Cultural interpretation

To explore not just **what books existed**, but **which ones mattered and why they lasted**.

