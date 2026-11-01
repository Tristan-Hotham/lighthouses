"""Geography: sea coastline length for every country and every first-level region, a sea-coast line set for the
distance test, a light world outline for the page and figures, and town names.

Coastline method. A country's sea coast is the part of its Natural Earth 1:10m outline that is not shared with a
neighbour: its boundary minus every neighbouring country (buffered by about 300 m to absorb slivers). Natural Earth's
standard country polygons fill lakes, so lake shores are not counted as coast; the Caspian Sea, which is outside the
polygons, is. Lengths are geodesic (WGS84 ellipsoid). The same method on the 1:10m states and provinces gives the
coast of each region. Coastlines are fractal: at 1:10m, fjords and skerries are smoothed away, so these are lengths at
one fixed scale, good for comparing countries, not 'true' lengths."""
from shapely.geometry import shape, mapping, MultiLineString, LineString
from shapely.strtree import STRtree
from shapely.ops import unary_union
from shapely import get_parts
from pyproj import Geod
from common import *

GD = Geod(ellps="WGS84")
iso_of = lambda p: MERGE.get(p["ADM0_A3"], p["ADM0_A3"])


def km(g):
    return GD.geometry_length(g) / 1000 if not g.is_empty else 0.0


def coasts(geoms):
    tree = STRtree(geoms)
    out = []
    for i, g in enumerate(geoms):
        nb = [geoms[j] for j in tree.query(g.buffer(0.01)) if j != i]
        b = g.boundary
        if nb:
            b = b.difference(unary_union(nb).buffer(0.003))
        out.append(b)
    return out


# ---- countries (Natural Earth 1:10m map units; Aland merged into Finland)
C10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]
cg, cname, cprops = {}, {}, {}
for f in C10:
    p = f["properties"]; iso = iso_of(p)
    g = shape(f["geometry"]).buffer(0)
    cg[iso] = cg[iso].union(g) if iso in cg else g
    if iso not in cname or iso == p["ADM0_A3"]:
        nm = p["NAME_EN"] or p["ADMIN"]
        cname[iso] = {"United States of America": "United States", "People's Republic of China": "China", "The Bahamas": "Bahamas",
                      "Republic of the Congo": "Congo", "Democratic Republic of the Congo": "DR Congo", "Federated States of Micronesia": "Micronesia",
                      "Turkey": "Turkey", "Republic of Ireland": "Ireland", "Kingdom of the Netherlands": "Netherlands", "The Gambia": "Gambia"}.get(nm, nm)
        cprops[iso] = {"sov": p["SOVEREIGNT"], "cont": p["CONTINENT"], "type": p["TYPE"]}
isos = sorted(cg)
geoms = [cg[i] for i in isos]
cc = coasts(geoms)
coast_km = {i: round(km(c), 1) for i, c in zip(isos, cc)}
print("countries", len(isos), "with coast", sum(1 for v in coast_km.values() if v > 0), "world coast km", round(sum(coast_km.values())))

# all sea-coast lines, split into short pieces for a fast nearest-line search
pieces = []
for c in cc:
    for ln in get_parts(c):
        if ln.geom_type == "LineString":
            xy = list(ln.coords)
            for k in range(0, len(xy) - 1, 20):
                seg = xy[k:k + 21]
                if len(seg) >= 2:
                    pieces.append(seg)
jsave({"pieces": pieces}, f"{WORK}/coast_pieces.json")
print("coast pieces", len(pieces))

# country polygons for the point-in-country test (simplified slightly)
jsave({"isos": isos, "geoms": [mapping(g.simplify(0.002, preserve_topology=True)) for g in geoms]}, f"{WORK}/countries10.json")

# ---- first-level regions (states, provinces, counties)
A1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
rg, rinfo = [], []
for f in A1:
    p = f["properties"]
    try:
        g = shape(f["geometry"]).buffer(0)
    except Exception:
        continue
    if g.is_empty:
        continue
    rg.append(g)
    a3 = MERGE.get(p.get("adm0_a3"), p.get("adm0_a3"))
    rinfo.append({"id": p.get("adm1_code") or p.get("iso_3166_2"), "name": p.get("name_en") or p.get("name"), "iso": a3,
                  "type": p.get("type_en") or p.get("type") or ""})
rc = coasts(rg)
for r, c, g in zip(rinfo, rc, rg):
    r["coast_km"] = round(km(c), 1)
    r["area_km2"] = None
jsave({"regions": rinfo, "geoms": [mapping(g.simplify(0.002, preserve_topology=True)) for g in rg]}, f"{WORK}/regions10.json")
print("regions", len(rinfo), "with coast", sum(1 for r in rinfo if r["coast_km"] > 0))

jsave({"cname": cname, "coast_km": coast_km, "props": cprops}, f"{WORK}/countries.json")


# ---- page and figure outline: Natural Earth 1:50m, simplified
def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, cpos = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = MERGE.get(p["ADM0_A3"], p["ADM0_A3"])
    gs = shape(f["geometry"]).simplify(0.03, preserve_topology=True)
    if gs.is_empty:
        continue
    gm = mapping(gs)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    cpos[iso] = [round(p["LABEL_X"], 2), round(p["LABEL_Y"], 2), float(p["POP_EST"] or 0)]
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")
jsave(cpos, f"{WORK}/cpos.json")

P = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")
cities = []
for f in P["features"]:
    p = f["properties"]; pop = p.get("pop_max") or 0
    if pop >= 100000 or p.get("adm0cap") == 1:
        cities.append({"name": re.sub(r"\s+", " ", p["name"]), "lat": round(p["latitude"], 3), "lon": round(p["longitude"], 3), "pop": int(pop)})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB; cities", len(cities))
for i in ("SWE", "FIN", "USA", "GBR", "NOR", "CAN", "AUS", "IDN", "GRL", "JPN", "FRA", "DEU"):
    print(i, cname[i], coast_km[i])
