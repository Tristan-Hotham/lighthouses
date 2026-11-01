"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23857614, https://doi.org/10.5281/zenodo.23857614 and https://blog.tristanhotham.com/2026/10/31/lighthouses/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Lighthouses_of_the_World"
T, CO, RG = R["timeline"], R["country"], R["regions"]
B = CO["by_iso"]

# the page build checks the shared facts; these are numbers written in words or in alt text in the blog
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
assert [B[i]["n"] for i in ("SWE", "USA", "FIN", "CAN", "GBR")] == [2555, 923, 794, 473, 468]
assert [round(c["per1000"]) for c in CO["dense"][:4]] == [341, 126, 85, 71] and 39 <= min(B[i]["per1000"] for i in ("NLD", "PRT", "FRA", "ESP", "GBR")) and max(B[i]["per1000"] for i in ("NLD", "PRT", "FRA", "ESP", "GBR")) <= 52
assert 39 <= B["GBR"]["per1000"] and B["FRA"]["per1000"] <= 48.5                                    # "between about 39 and 48"
assert T["swe_peak_n"] == 326 and T["all_2020s"] == 51
tot = dict(zip(T["decades"], T["total"])); assert all(290 <= tot[d] <= 500 for d in range(1850, 1970, 10)) and all(100 <= tot[d] <= 220 for d in (1980, 1990, 2000, 2010))
assert [round(r["per100"], 1) for r in RG["top_outside_nordic"][:5]] == [13.8, 12.9, 11.7, 11.0, 10.9] and RG["top"][0]["per100"] == 71.9 and 20.5 < RG["top"][11]["per100"] < 21.5
assert [r["name"] for r in RG["top_outside_nordic"][:5]] == ["Lower Saxony", "Connecticut", "Bizerte", "Finistère", "Livorno"]
tl = R["tallest"]["rows"]; assert (tl[0]["m"], tl[1]["m"], tl[2]["m"], tl[-1]["m"], len(tl)) == (83, 76, 75, 60, 28)
assert [c["name"] for c in R["coverage"]["most_bare"]] == ["Madagascar", "Sweden", "Peru", "Mexico", "Finland", "China", "Egypt", "Tunisia"] and all(c["sl_le1_pct"] > 80 for c in R["coverage"]["most_bare"])
assert sorted(c["name"] for c in R["coverage"]["least_bare"]) == sorted(["Estonia", "Spain", "Croatia", "Portugal", "United States", "Argentina"]) and all(c["sl_le1_pct"] < 20 for c in R["coverage"]["least_bare"])
assert R["n"]["dropped"] < 50                                                                          # "a few dozen"

post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
assert set(re.findall(r"\{\{(?!IMG)[^}]*\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23857614"}
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Lighthouses of the world: every light on one glowing map",
        "slug": "lighthouses",
        "excerpt": f"Wikidata knows of {R['n']['items']:,} lighthouses. I mapped them all and switched them on. Most were built in the industrial century, the oldest still standing is Roman, and the brightest coast belongs to Sweden, partly because Sweden wrote its lights down.",
        "seo_description": f"{R['n']['items']:,} lighthouses on one glowing map: where they are per km of coast, when they were built, the oldest still standing and the tallest.",
        "tags": ["lighthouses", "maps", "data visualisation", "maritime history", "Wikidata", "coastlines", "open data"],
        "header_alt": f"Title card reading 'Lighthouses of the world' in black and amber on pale paper, beside a dark night map of northern Europe where every lighthouse glows amber and the Swedish and Finnish coasts form bright lines. Text: every lighthouse in Wikidata, {R['n']['items']:,} of them; AD {R['spot']['Tower of Hercules']['year']}, Tower of Hercules, oldest still standing; {CO['dense'][0]['per1000']:.0f} lights per 1,000 km of coast in Sweden."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/lighthouses_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"lighthouses/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"lighthouses/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "lighthouses/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ")
zmeta = {"title": "Lighthouses of the World: Where They Stand, When They Were Built, the Oldest and the Tallest",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Data: Wikidata (CC0); Wikipedia contributors, List of tallest lighthouses (CC BY-SA 4.0; the derived table is shared under the same licence); Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["lighthouses", "maritime history", "navigation", "Wikidata", "coastline length", "Natural Earth", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://en.wikipedia.org/wiki/List_of_tallest_lighthouses", "relation": "isDerivedFrom", "resource_type": "other"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

# Reddit post (numbers from results.json)
SW = B["SWE"]
post_md = f"""## Title

[OC] Every lighthouse in Wikidata, {R['n']['items']:,} of them, on one map: outside Sweden, building peaked in the {T['peak_dec_nosw']}s, and the oldest still standing is Roman (AD {R['spot']['Tower of Hercules']['year']})

## Body

I mapped every Wikidata item that is a lighthouse and has coordinates ({R['n']['items']:,} after removing keepers' houses and replicas) and coloured them by the year they were built or first lit. Outside Sweden, new lights rise from {T['nosw_1820s']} in the 1820s to {T['peak_n_nosw']} in the {T['peak_dec_nosw']}s and fall to about {T['nosw_1970_2019_avg']} a decade after 1970 (automation, then satellite navigation). Per 1,000 km of coast (Natural Earth 1:10m), Sweden has {SW['per1000']:.0f} lights against {CO['world_per1000']:.1f} for the world. The big caveat: Wikidata coverage varies by country. Sweden's {SW['n']:,} lights ({CO['swe_pct']:.0f}% of the total) look like a national list loaded in full ({SW['sl_le1_pct']:.0f}% have at most one Wikipedia article), while Indonesia has {B['IDN']['n']} and Nigeria none. Tallest heights come from Wikipedia's list because the Wikidata heights I had lost their units. Interactive map with a night glow view and search: {PAGE}

## Source comment

Sources: Wikidata (CC0), every item that is an instance of lighthouse (Q39715) or a subclass with coordinates, via QLever; Wikipedia contributors, List of tallest lighthouses (CC BY-SA 4.0); Natural Earth 1:10m countries and states (public domain), used to measure each coast as the country outline minus shared borders. Dates are Wikidata's earliest inception year, often the first light on the site rather than the present tower. "Still standing" was checked by hand for the oldest towers.

Tools: Python (pandas, shapely, pyproj, scipy, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in post_md, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post_md)
print("post.md written")
