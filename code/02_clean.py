"""Clean the Wikidata lighthouse extract: one row per item, a country and region by location, sea or inland, the
earliest inception year, and raw heights (unit unknown). Writes data/lighthouses.csv."""
import math
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point, LineString
from shapely.strtree import STRtree
from pyproj import Geod
from common import *

GD = Geod(ellps="WGS84")
T = pd.read_csv(f"{RAW}/wikidata_lighthouses.tsv", sep="\t", dtype=str, quoting=3)
T.columns = [c.lstrip("?") for c in T.columns]
n_rows = len(T)
T["qid"] = T.b.str.extract(r"entity/(Q\d+)>")[0]
strip = lambda s: None if not isinstance(s, str) else re.sub(r'^"(.*)"(@[\w-]+)?$', r"\1", s).replace('\\"', '"')
T["label"] = T.bL.map(strip)
T["country_wd"] = T.cL.map(strip)
xy = T.coord.str.extract(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)")
T["lon"] = xy[0].astype(float); T["lat"] = xy[1].astype(float)
T["year"] = pd.to_numeric(T.inc.str.extract(r'^"?(-?\d{1,4})-\d\d-\d\d')[0], errors="coerce")   # blank-node (unknown value) dates give NaN
T["h"] = pd.to_numeric(T.h, errors="coerce"); T["fh"] = pd.to_numeric(T.fh, errors="coerce"); T["sl"] = T.sl.astype(int)
n_unknown_inc = int((T.inc.notna() & T.year.isna()).sum())


def uniq(s):
    return sorted({x for x in s if x == x and x is not None})


rows = []
for q, g in T.groupby("qid", sort=False):
    ys = uniq(g.year); hs = uniq(g.h); fhs = uniq(g.fh); cs = uniq(g.country_wd)
    lab = next((x for x in g.label if isinstance(x, str) and x), None)
    rows.append({"qid": q, "name": lab, "sitelinks": int(g.sl.max()), "lat": float(g.lat.iloc[0]), "lon": float(g.lon.iloc[0]),
                 "n_coords": int(g[["lat", "lon"]].drop_duplicates().shape[0]), "country_wd": "|".join(cs),
                 "year": int(min(ys)) if ys else None, "year_all": "|".join(str(int(y)) for y in ys),
                 "height_raw": "|".join(f"{v:g}" for v in hs), "focal_raw": "|".join(f"{v:g}" for v in fhs)})
D = pd.DataFrame(rows)
nocoord = D.lat.isna() | D.lon.isna()          # coordinates given as "unknown value"
n_nocoord = int(nocoord.sum()); D = D[~nocoord].reset_index(drop=True)
# buildings at light stations that Wikidata types as lighthouses (keepers' houses, barrack blocks) and modern replicas
NOT_TOWER = r"(?i)keeper|accommodation block|barrack block|\breplica\b"
drop = D.name.fillna("").str.contains(NOT_TOWER)
n_dropped = int(drop.sum()); dropped_examples = sorted(D[drop].name)[:6]
D = D[~drop].reset_index(drop=True)
print("rows", n_rows, "items", len(D), "dropped", n_dropped)

# ---- country and region by location
C = jload(f"{WORK}/countries.json"); CN = jload(f"{WORK}/countries10.json")
cgeo = [shape(g) for g in CN["geoms"]]; ctree = STRtree(cgeo)
RG = jload(f"{WORK}/regions10.json"); rgeo = [shape(g) for g in RG["geoms"]]; rtree = STRtree(rgeo)
PC = jload(f"{WORK}/coast_pieces.json")["pieces"]
lines = [LineString(p) for p in PC]; ltree = STRtree(lines)


def gdist(pt, geom):
    """Geodesic km from a point to the nearest point of a geometry (nearest found in a local equirectangular frame)."""
    k = math.cos(math.radians(pt.y))
    from shapely import affinity
    g2 = affinity.scale(geom, xfact=k, yfact=1, origin=(0, 0)); p2 = Point(pt.x * k, pt.y)
    from shapely.ops import nearest_points
    a = nearest_points(p2, g2)[1]
    return GD.inv(pt.x, pt.y, a.x / k, a.y)[2] / 1000


wd2iso = {v: k for k, v in C["cname"].items()}
wd2iso.update({"People's Republic of China": "CHN", "Russian Empire": "RUS", "Kingdom of the Netherlands": "NLD", "Kingdom of Denmark": "DNK",
               "Republic of Ireland": "IRL", "State of Palestine": "PSX", "Turkey": "TUR", "Sahrawi Arab Democratic Republic": "SAH", "Taiwan": "TWN"})
iso, how, land, dsea, reg = [], [], [], [], []
for r in D.itertuples():
    pt = Point(r.lon, r.lat)
    hit = [j for j in ctree.query(pt) if cgeo[j].contains(pt)]
    if hit:
        iso.append(CN["isos"][hit[0]]); how.append("inside"); land.append(True)
    else:
        cand = ctree.query(pt.buffer(0.6))
        best = min(((gdist(pt, cgeo[j]), j) for j in cand), default=(1e9, None))
        if best[0] <= NEAR_KM:
            iso.append(CN["isos"][best[1]]); how.append("nearest"); land.append(False)
        else:
            w = (r.country_wd or "").split("|")[0]
            iso.append(wd2iso.get(w)); how.append("wikidata" if wd2iso.get(w) else "none"); land.append(False)
    # distance to the sea coast
    cand = ltree.query(pt.buffer(0.35))
    d = min((gdist(pt, lines[j]) for j in cand), default=99.0)
    dsea.append(round(d, 2))
    rh = [j for j in rtree.query(pt) if rgeo[j].contains(pt)]
    if not rh:
        cand = rtree.query(pt.buffer(0.3))
        best = min(((gdist(pt, rgeo[j]), j) for j in cand), default=(1e9, None))
        rh = [best[1]] if best[0] <= NEAR_KM else []
    reg.append(RG["regions"][rh[0]]["id"] if rh else None)
D["iso"] = iso; D["country"] = [C["cname"].get(i, "Not assigned") if i else "Not assigned" for i in iso]
D["country_how"] = how; D["on_land"] = land; D["km_to_sea_coast"] = dsea; D["region_id"] = reg
D["setting"] = np.where(D.on_land & (D.km_to_sea_coast > SEA_KM), "inland", "sea")
D["era"] = [era_of(y) for y in D.year]
D = D.sort_values(["iso", "qid"], na_position="last").reset_index(drop=True)
D.to_csv(f"{DATA}/lighthouses.csv", index=False)
jsave({"n_rows": n_rows, "n_unknown_inc": n_unknown_inc, "n_dropped": n_dropped, "n_nocoord": n_nocoord, "n_items_raw": len(D) + n_dropped + n_nocoord}, f"{WORK}/clean_meta.json")
print(len(D), "items;", n_nocoord, "without coordinates")
