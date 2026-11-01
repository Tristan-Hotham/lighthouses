"""README.md and LICENSE, numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
n, T, CO, RG, TL = R["n"], R["timeline"], R["country"], R["regions"], R["tallest"]
B = CO["by_iso"]
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
readme = f"""# Lighthouses of the world

Every lighthouse in Wikidata, {n['items']:,} of them, on one map that glows like a coastline at night: where they are, measured against the length of each country's coast, when they were built, the oldest still standing and the tallest. Built from Wikidata, Wikipedia's List of tallest lighthouses and Natural Earth.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Wikidata has {n['items']:,} lighthouses with a position in {n['countries']} countries and territories, {n['dated']:,} of them dated. Sweden has {B['SWE']['n']:,} ({CO['swe_pct']:.0f}% of the total), the United States {B['USA']['n']}, Finland {B['FIN']['n']}, Canada {B['CAN']['n']} and the United Kingdom {B['GBR']['n']}.
- Per 1,000 km of sea coast (Natural Earth 1:10m): Sweden {CO['dense'][0]['per1000']:.0f}, Finland {CO['dense'][1]['per1000']:.0f}, Tunisia {CO['dense'][2]['per1000']:.0f}, Germany {CO['dense'][3]['per1000']:.0f}; the world {CO['world_per1000']:.1f}. Canada has {B['CAN']['per1000']:.1f} and Indonesia {B['IDN']['per1000']:.1f}.
- The densest regional coasts are all Swedish or Finnish, led by Västra Götaland ({RG['top'][0]['per100']:.1f} sea lights per 100 km). Outside those two countries: {RG['top_outside_nordic'][0]['name']} ({RG['top_outside_nordic'][0]['per100']:.1f}) and {RG['top_outside_nordic'][1]['name']} ({RG['top_outside_nordic'][1]['per100']:.1f}).
- Building: outside Sweden, new lights rise from {T['nosw_1820s']} in the 1820s to {T['peak_n_nosw']} in the {T['peak_dec_nosw']}s, stay above 300 a decade until the 1910s and fall to about {T['nosw_1970_2019_avg']} a decade in 1970 to 2019. Sweden's register adds a second wave that peaks in the {T['swe_peak_dec']}s ({T['swe_peak_n']}).
- Oldest: the oldest dated light still standing is the Tower of Hercules, A Coruña ({fmt(R['spot']['Tower of Hercules']['year'], 'yr')}); older dates belong to the lost Pharos of Alexandria ({fmt(R['spot']['Lighthouse of Alexandria']['year'], 'yr')}) and Tower of Caepio. Tallest (Wikipedia list): Île Vierge, France, {TL['top']['m']} m ({TL['top']['year']}).
- Coverage: {n['sl_le1_pct']:.0f}% of the lights have at most one Wikipedia article; {B['SWE']['sl_le1_pct']:.0f}% in Sweden and {B['FIN']['sl_le1_pct']:.0f}% in Finland (bulk imports of national lists) against {B['USA']['sl_le1_pct']:.0f}% in the United States. Greenland, Nigeria, Kenya, Ecuador and the United Arab Emirates have none in Wikidata. The map shows the record as much as the sea.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/lighthouses.csv` | {n['items']:,} lighthouses: Wikidata id, English name, sitelinks, point, Wikidata country, earliest inception year and all years, raw height and focal height (unit not given), country by location and how assigned, km to the sea coast, sea or inland, region ({size('lighthouses.csv')}). |
| `data/by_country.csv` | Lights, sea and inland lights, dated lights, coast length, sea lights per 1,000 km and bare-record share per country. |
| `data/regions_coast.csv` | Coast length and sea lights for every first-level region with a coast. |
| `data/by_decade.csv` | Dated lights per decade, 1700 to the 2020s, by country group. |
| `data/tallest_wikipedia.csv` | The {TL['n']} towers in Wikipedia's List of tallest lighthouses, matched to Wikidata (CC BY-SA 4.0). |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/points.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Lighthouses: every Wikidata item that is an instance of lighthouse (Q39715) or a subclass and has coordinates ({n['items_raw']:,} items from {n['rows']:,} rows). Removed {n['dropped']} keepers' houses, barrack blocks and replicas and {n['nocoord']} item with an unknown position. Earliest inception year where there are several.
- Country: the Natural Earth 1:10m map unit containing the light, else the nearest within {R['meta']['near_km']:.0f} km, else Wikidata's country. Dependencies count on their own; Åland merged into Finland.
- Sea and inland: lights on land more than {R['meta']['sea_km']:.0f} km from the sea coast are lake and river lights ({n['inland']:,}) and are left out of per-coast figures.
- Coast length: each 1:10m country (and state or province) outline minus every stretch within about 300 m of a neighbour, measured on the WGS84 ellipsoid. Lakes are inside Natural Earth's country polygons, so lake shores do not count. Coastlines are scale dependent; these lengths compare places at one scale.
- Oldest: Wikidata inception years. Whether a tower still stands was checked by hand for the {n['oldest_checked']} best known of the oldest; the rest are marked "not checked".
- Tallest: Wikipedia's List of tallest lighthouses. Wikidata heights were extracted without units (metres or feet) and are shown with a warning only.
- Caveats: Wikidata coverage varies hugely by country; inception dates may be the first light on the site; coast lengths depend on scale.

## How to rerun

Needs Python 3 with pandas, shapely, pyproj, scipy, matplotlib, fontTools and Pillow, xelatex and pdftotext; node with Playwright for QA. Raw inputs are read in place from `{RAW}/` and `{GEO}/` (set in `code/common.py`): `wikidata_lighthouses.tsv` (Wikidata via QLever, retrieved {RETRIEVED}), `wiki_List_of_tallest_lighthouses.json` (Wikipedia page HTML) and Natural Earth GeoJSON. Intermediate files go to `/dev/shm/lighthouses/work` (set `LHTMP` to change).

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
- Wikipedia contributors, "List of tallest lighthouses" (https://en.wikipedia.org/wiki/List_of_tallest_lighthouses), revision {TL['revid']}. CC BY-SA 4.0; `data/tallest_wikipedia.csv` is shared under the same licence.
- Natural Earth (https://www.naturalearthdata.com/) countries, states and provinces and populated places. Public domain.
- Base map tiles on the page: © Esri and its partners.

## Citation

Hotham, T. (2026) Lighthouses of the world: where they stand, when they were built, the oldest and the tallest, from Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
LIC = """Code (everything in code/ and reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data (data/, release/, reddit/*.png, header.png, index.html text): Creative Commons Attribution 4.0
International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/. Attribution: Tristan Hotham (2026).
Exception: data/tallest_wikipedia.csv is derived from Wikipedia (Wikipedia contributors, CC BY-SA 4.0) and is shared under
CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/.

Third-party data: Wikidata content is CC0. Wikipedia text is CC BY-SA 4.0. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)
print("README", len(readme.split()), "words")
