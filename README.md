# Lighthouses of the world

Every lighthouse in Wikidata, 9,770 of them, on one map that glows like a coastline at night: where they are, measured against the length of each country's coast, when they were built, the oldest still standing and the tallest. Built from Wikidata, Wikipedia's List of tallest lighthouses and Natural Earth.

Interactive page: https://maps.tristanhotham.com/lighthouses/
Paper: https://doi.org/10.5281/zenodo.23857614
Blog post: https://blog.tristanhotham.com/2026/10/31/lighthouses/

## Headline results

- Wikidata has 9,770 lighthouses with a position in 162 countries and territories, 6,546 of them dated. Sweden has 2,555 (26% of the total), the United States 923, Finland 794, Canada 473 and the United Kingdom 468.
- Per 1,000 km of sea coast (Natural Earth 1:10m): Sweden 341, Finland 126, Tunisia 85, Germany 71; the world 9.4. Canada has 2.9 and Indonesia 0.2.
- The densest regional coasts are all Swedish or Finnish, led by Västra Götaland (71.9 sea lights per 100 km). Outside those two countries: Lower Saxony (13.8) and Connecticut (12.9).
- Building: outside Sweden, new lights rise from 103 in the 1820s to 376 in the 1870s, stay above 300 a decade until the 1910s and fall to about 97 a decade in 1970 to 2019. Sweden's register adds a second wave that peaks in the 1940s (326).
- Oldest: the oldest dated light still standing is the Tower of Hercules, A Coruña (AD 100); older dates belong to the lost Pharos of Alexandria (278 BC) and Tower of Caepio. Tallest (Wikipedia list): Île Vierge, France, 83 m (1902).
- Coverage: 60% of the lights have at most one Wikipedia article; 96% in Sweden and 91% in Finland (bulk imports of national lists) against 16% in the United States. Greenland, Nigeria, Kenya, Ecuador and the United Arab Emirates have none in Wikidata. The map shows the record as much as the sea.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/lighthouses.csv` | 9,770 lighthouses: Wikidata id, English name, sitelinks, point, Wikidata country, earliest inception year and all years, raw height and focal height (unit not given), country by location and how assigned, km to the sea coast, sea or inland, region (1.2 MB). |
| `data/by_country.csv` | Lights, sea and inland lights, dated lights, coast length, sea lights per 1,000 km and bare-record share per country. |
| `data/regions_coast.csv` | Coast length and sea lights for every first-level region with a coast. |
| `data/by_decade.csv` | Dated lights per decade, 1700 to the 2020s, by country group. |
| `data/tallest_wikipedia.csv` | The 28 towers in Wikipedia's List of tallest lighthouses, matched to Wikidata (CC BY-SA 4.0). |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/points.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Lighthouses: every Wikidata item that is an instance of lighthouse (Q39715) or a subclass and has coordinates (9,810 items from 11,614 rows). Removed 39 keepers' houses, barrack blocks and replicas and 1 item with an unknown position. Earliest inception year where there are several.
- Country: the Natural Earth 1:10m map unit containing the light, else the nearest within 30 km, else Wikidata's country. Dependencies count on their own; Åland merged into Finland.
- Sea and inland: lights on land more than 5 km from the sea coast are lake and river lights (1,075) and are left out of per-coast figures.
- Coast length: each 1:10m country (and state or province) outline minus every stretch within about 300 m of a neighbour, measured on the WGS84 ellipsoid. Lakes are inside Natural Earth's country polygons, so lake shores do not count. Coastlines are scale dependent; these lengths compare places at one scale.
- Oldest: Wikidata inception years. Whether a tower still stands was checked by hand for the 17 best known of the oldest; the rest are marked "not checked".
- Tallest: Wikipedia's List of tallest lighthouses. Wikidata heights were extracted without units (metres or feet) and are shown with a warning only.
- Caveats: Wikidata coverage varies hugely by country; inception dates may be the first light on the site; coast lengths depend on scale.

## How to rerun

Needs Python 3 with pandas, shapely, pyproj, scipy, matplotlib, fontTools and Pillow, xelatex and pdftotext; node with Playwright for QA. Raw inputs are read in place from `/home/claude/newdata/raw8/lighthouses/` and `/home/claude/newdata/raw/geo/` (set in `code/common.py`): `wikidata_lighthouses.tsv` (Wikidata via QLever, retrieved 2026), `wiki_List_of_tallest_lighthouses.json` (Wikipedia page HTML) and Natural Earth GeoJSON. Intermediate files go to `/dev/shm/lighthouses/work` (set `LHTMP` to change).

```
python3 code/01_geo.py         # coast lengths, outlines, town names (about 6 minutes)
python3 code/02_clean.py       # one row per lighthouse, country, sea or inland
python3 code/03_results.py     # results.json, tables, page data
python3 code/04_build_site.py  # index.html (checks every fact stated in words)
python3 code/05_figures.py     # header, blog and paper figures
python3 code/06_paper.py       # paper PDF
python3 code/07_readme.py      # README and LICENSE
python3 code/08_release.py     # blog post, Zenodo files
python3 reddit/collage.py      # collage
node code/qa.js                # screenshots (with python3 -m http.server 8795 running)
```

## Sources and licences

- Wikidata (https://www.wikidata.org/), via QLever (https://qlever.cs.uni-freiburg.de/). CC0.
- Wikipedia contributors, "List of tallest lighthouses" (https://en.wikipedia.org/wiki/List_of_tallest_lighthouses), revision 1306705349. CC BY-SA 4.0; `data/tallest_wikipedia.csv` is shared under the same licence.
- Natural Earth (https://www.naturalearthdata.com/) countries, states and provinces and populated places. Public domain.
- Base map tiles on the page: © Esri and its partners.

## Citation

Hotham, T. (2026) Lighthouses of the world: where they stand, when they were built, the oldest and the tallest, from Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23857614

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
