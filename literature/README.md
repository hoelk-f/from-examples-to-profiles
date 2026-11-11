# Taxonomy literature search and evidence

This directory documents the literature search and evidence assessment supporting the taxonomy. The literature basis combines a targeted, non-systematic search on PBE data transformations, generalization, and functional testing with previously known relevant work. Search records document candidate screening and full-text assessment. The taxonomy evidence records link its dimensions and categories to relevant source passages and distinguish source findings from our interpretation. The search does not claim exhaustive coverage or independent duplicate screening.

Ten queries were run on 5 October 2026 through general web search, without date, language or domain filters. The search backend and ranking parameters were not disclosed. Eight returned positions per query were screened, giving 80 screened hits. Eighteen were excluded and 23 were duplicate discovery paths, leaving 39 candidate groups. In query order and then result order, 24 suitable candidates were selected for full-text review. The remaining 15 were deferred because the review budget was exhausted, not excluded for irrelevance. This order favors the earlier query topics.

Original passages were accessible for 23 of the 24 selected candidates. Seventeen supplied relevant evidence, four clarified scope boundaries, two were excluded after full-text inspection and one remained unavailable. Exact-title searches and alternative author copies were used only to obtain already selected works. Search rankings may change. The recorded hits and decisions allow the original selection to be reconstructed.

| File | Contents |
| --- | --- |
| `search/queries.csv` | Ten exact queries in order |
| `search/hits.csv` | All 241 returned entries and screening positions |
| `search/screening.csv` | Decisions for the 80 screened hits |
| `search/candidates.csv` | Deduplication, review order and all 39 final statuses |
| `search/retrieval_log.csv` | Full-text access attempts and outcomes |
| `search/evidence.csv` | Assessment of 24 full-text candidates, bibliographic identity, passage locations and limits |
| `taxonomy_evidence.csv`, `taxonomy_references.bib` | Passage evidence and bibliography for 23 taxonomy sources |
| `search/taxonomy_source_crosswalk.csv` | Links between taxonomy sources and screened search results |
| `chapter_sources.csv` | Source routes, evidence links and limits for the 19 cited taxonomy chapter sources |

The crosswalk links the taxonomy evidence set to the screened search results. In the chapter records, `source_route` indicates whether a source was previously known or also retrieved by the search. Citation keys for known work are retained where available. Source PDFs are not redistributed.

Run `reproduce verify` from the repository root to check file integrity and selection counts.
