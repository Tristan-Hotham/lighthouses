"""Shared paths and helpers for the lighthouses project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw8/lighthouses/wikidata_lighthouses.tsv
      Wikidata (CC0), queried through QLever: every item that is an instance of lighthouse (Q39715) or a subclass, with
      coordinates (P625). Columns: item, English label, number of sitelinks, coordinates, country (P17) English label,
      inception (P571), height (P2048) and focal height (P2923). Rows repeat when an item has several values. The
      extract keeps the amounts of P2048 and P2923 but NOT their units (metres or feet). Retrieved 2026.
  /home/claude/newdata/raw8/lighthouses/wiki_List_of_tallest_lighthouses.json
      English Wikipedia, "List of tallest lighthouses" (parsed HTML and revision id). Wikipedia contributors, CC BY-SA 4.0.
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_10m_admin_1_states_provinces.geojson,
      ne_50m_admin_0_countries.geojson, ne_10m_populated_places_simple.geojson
      Natural Earth (public domain): coastline lengths, countries, regions, map outlines and town names.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("LH_RAW", "/home/claude/newdata/raw8/lighthouses")
GEO = os.environ.get("LH_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("LH_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("LHTMP", "/dev/shm/lighthouses"), "work")
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "lighthouses"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23857614"                 # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/lighthouses/"           # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# when the light was first lit, by Wikidata inception (order = legend order); last = not dated
ERAS = [("Before 1700", "#6B3FA0", -9999, 1699), ("1700 to 1799", "#2F6FB0", 1700, 1799),
        ("1800 to 1849", "#1E9E8E", 1800, 1849), ("1850 to 1899", "#E3A21A", 1850, 1899),
        ("1900 to 1949", "#E0662B", 1900, 1949), ("1950 on", "#B3202A", 1950, 2100), ("Not dated", "#A8A397", None, None)]
SEA_KM = 5.0      # a lighthouse more than this far inland from the Natural Earth sea coast counts as a lake or river light
NEAR_KM = 30.0    # an offshore light is given the nearest country if one lies within this distance
MERGE = {"ALD": "FIN"}   # Natural Earth map units merged into their country (Aland into Finland)


def era_of(y):
    if y is None or y != y:
        return len(ERAS) - 1
    for i, e in enumerate(ERAS[:-1]):
        if e[2] <= y <= e[3]:
            return i
    return len(ERAS) - 1


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return f"{-int(v)} BC" if int(v) < 0 else (f"AD {int(v)}" if int(v) < 1000 else str(int(v)))
    raise ValueError(f)


def fill(text, R, keep=("DOI", "BLOG_URL", "DOI_URL")):
    """Replace {{path|format}} tokens with numbers from results.json; leave publisher placeholders alone."""
    def rep(m):
        if m.group(1) in keep or m.group(1).startswith("IMG"):
            return m.group(0)
        return fmt(get(R, m.group(1)), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)
