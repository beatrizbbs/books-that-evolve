# Findings Draft

This draft turns the exploratory charts and tables into candidate arguments. It is written for reuse in the README or analysis notebook.

## Era Summaries

**1997-2008 · The Middle Grade Fantasy Era**  
Harry Potter and Percy Jackson anchor a period where middle grade fantasy dominates Goodreads cultural memory. School, magic, quests, and wonder define youth fiction's most visible early peak.

**2009-2013 · The Paranormal Wave**  
Paranormal / Supernatural becomes the leading theme, while Paranormal Romance rises beside it. Twilight, Cassandra Clare, Vampire Academy, and related series push supernatural love stories and urban fantasy to the center.

**2014-2018 · The Mixed Speculative Era**  
Dystopia remains one of the era's most recognizable science-fiction modes through The Hunger Games, Divergent, and The Selection. The broader Science Fiction bucket ranks first overall, while fantasy shifts toward kingdoms, courts, empires, and romance-adjacent secondary worlds.

**2019-2021 · The High Fantasy Turn**  
Epic / High Fantasy leads the smaller recent sample, and Romantasy reaches its highest era share at 5.9%. Sarah J. Maas, Leigh Bardugo, Holly Black, and other series authors shape the top-ranked books.

## Key Findings

1. **Middle grade fantasy anchors the earliest era.**  
   In 1997-2008, Middle Grade Fantasy is the largest theme by weighted popularity share at 36.8%, far ahead of Science Fiction at 17.0% and Epic / High Fantasy at 15.1%. The top books in this era are heavily shaped by Harry Potter, Percy Jackson, and other series-driven fantasy titles.

2. **Paranormal and paranormal romance peak in the 2009-2013 era.**  
   Paranormal / Supernatural becomes the leading theme in 2009-2013 with 24.2% of weighted popularity. Paranormal Romance also reaches 16.4%, making the period clearly distinct from 1997-2008. The annual trend table shows both Paranormal / Supernatural and Paranormal Romance peaking in 2011.

3. **Dystopian fiction rises around the Hunger Games and Divergent moment, but it does not become the largest overall theme.**  
   Dystopian / Post-Apocalyptic reaches its highest annual book count in 2012 and its highest annual weighted popularity share in 2014. It is highly visible among era-defining books, especially through The Hunger Games and Divergent, but its era-level share remains below Paranormal, Science Fiction, Middle Grade Fantasy, and later Epic / High Fantasy.

4. **Science fiction is consistently present rather than confined to one short boom.**  
   Science Fiction is the second-ranked theme in 1997-2008 and 2009-2013, then becomes the top theme in 2014-2018 at 20.5%. This suggests that science-fictional framing persists across multiple waves, often overlapping with dystopian or speculative YA.

5. **Fantasy persists, but its center of gravity shifts.**  
   Early fantasy is dominated by Middle Grade Fantasy. By 2014-2018 and 2019-2021, Epic / High Fantasy becomes more prominent, while tracked keywords such as `kingdom`, `court`, `realm`, `queen`, `prince`, and `empire` rise after 2013. This supports a shift from school/magic-centered fantasy toward court, kingdom, and secondary-world vocabulary.

6. **Romantasy is visible but still smaller in this dataset.**  
   Romantasy grows from 2.2% of weighted popularity in 1997-2008 and 2009-2013 to 3.4% in 2014-2018 and 5.9% in 2019-2021. Its upward direction is meaningful, but the absolute counts remain modest compared with broader fantasy, paranormal, and science fiction categories.

7. **Era-defining books are strongly franchise-shaped.**  
   The top 12 books by popularity score in 1997-2008 are all tagged `blockbuster_franchise`; 2009-2013 and 2014-2018 each have 11 of their top 12 tagged that way. The highest-ranked books show how a small number of major series can define cultural memory even when the full theme distribution is broader.

8. **Removing the top 1% does not overturn the broad theme story.**  
   The top-1%-removed comparison reduces weighted popularity totals slightly, but the overall theme ordering remains similar. This means blockbuster titles strongly shape the visible canon and top-book lists, but the main era-level theme patterns are not solely artifacts of the highest-scoring books.

## Confident Findings

- **1997-2008 is dominated by Middle Grade Fantasy.**  
  Evidence: 36.8% weighted popularity share and 1,073 books tagged Middle Grade Fantasy in the era.

- **2009-2013 is the clearest paranormal era.**  
  Evidence: Paranormal / Supernatural is the top theme at 24.2%, and Paranormal Romance is third at 16.4%. Both peak annually in 2011.

- **Science Fiction remains important across eras.**  
  Evidence: it ranks second in 1997-2008 and 2009-2013, first in 2014-2018, and second in 2019-2021.

- **Franchise books dominate the top-ranked book lists.**  
  Evidence: top-12 era book tables are almost entirely series/franchise titles in the first three eras.

- **The broad theme distribution is not completely dependent on the top 1%.**  
  Evidence: top-1%-removed theme totals keep the same general ranking, with relatively small percentage changes by theme.

## Tentative Observations

- **Romantasy appears to rise after 2014, especially in 2019-2021.**  
  This is plausible and matches the top-book evidence around Sarah J. Maas, Leigh Bardugo, and fantasy romance-adjacent titles. However, the 2019-2021 sample is small, and the current `romantasy` rule is conservative.

- **Fantasy vocabulary seems to shift from school/magic language toward court/kingdom language.**  
  Keyword tables support this direction, especially after 2013, but description text is publisher- and metadata-dependent. This should be framed as textual evidence, not proof of a full market shift.

- **Dystopia spikes around 2012-2014 but may be partly absorbed into Science Fiction.**  
  Many dystopian books also carry science-fiction signals, so the categories overlap. The finding is real in the theme tags, but interpretation should acknowledge overlap.

- **The 2019-2021 era points toward Epic / High Fantasy, but it is underpowered.**  
  The era contains only 168 scoped books, compared with 1,504 to 2,897 books in earlier eras. Treat this period as directional rather than definitive.

- **Author concentration may reflect metadata and series structure.**  
  Some authors appear because they have many entries in long-running series. That is analytically useful for cultural-memory effects, but it should not be read as market share.

## Limitations

- **The dataset measures Goodreads visibility, not the full publishing market.**  
  These results describe books that accumulated attention, ratings, and list recognition on Goodreads. They should not be interpreted as all youth fiction published from 1997 to 2024.

- **Recent years are underrepresented.**  
  The realized scoped dataset effectively ends in 2021 and has far fewer books in 2019-2021 than in earlier periods. Findings about the newest era should be treated cautiously.

- **Theme tags are rule-based and overlapping.**  
  A book can belong to multiple themes, and some categories overlap naturally, especially Science Fiction with Dystopian / Post-Apocalyptic and Epic / High Fantasy with Romantasy.

- **Goodreads metadata is inconsistent.**  
  Genres, descriptions, series labels, and publication dates are user- or platform-dependent and may be missing, inconsistent, or edition-specific.

- **Popularity score reflects cultural memory within the dataset, not objective quality or sales.**  
  The score combines rating count, average rating, and Goodreads Best Books Ever votes. It is useful for visibility and affection, but it is not a sales measure.

- **Blockbuster/franchise tagging is approximate.**  
  The `series_flag` uses available series metadata, known franchise patterns, and popularity thresholds. It is useful for exploratory comparison but should be audited before making precise claims.

- **Keyword evolution depends on descriptions, not full book text.**  
  Keyword trends reflect title and description language. They capture how books are presented in metadata, not necessarily the complete vocabulary or themes of the books themselves.
