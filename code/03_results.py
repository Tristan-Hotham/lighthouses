"""Every number used in the page, paper, blog and collage (data/results.json), the reusable tables (data/*.csv) and the
page data (data/site.json embedded in the page, data/points.json loaded by it)."""
import io, html as H
from collections import Counter
import numpy as np
import pandas as pd
from common import *

D = pd.read_csv(f"{DATA}/lighthouses.csv", dtype={"name": str, "country_wd": str, "height_raw": str, "focal_raw": str, "year_all": str})
C = jload(f"{WORK}/countries.json"); CM = jload(f"{WORK}/clean_meta.json"); RG = jload(f"{WORK}/regions10.json")
pct = lambda a, b: round(100 * a / b, 1) if b else 0.0
N = len(D)
sea = D[D.setting == "sea"]
R = {"meta": {"page": PAGE, "repo": REPO, "retrieved": RETRIEVED, "sea_km": SEA_KM, "near_km": NEAR_KM}}

# ---------------------------------------------------------------- totals and coverage
dated = D.year.notna()
R["n"] = {"rows": CM["n_rows"], "items_raw": CM["n_items_raw"], "dropped": CM["n_dropped"], "nocoord": CM["n_nocoord"], "items": N, "dated": int(dated.sum()), "dated_pct": pct(dated.sum(), N), "undated": int((~dated).sum()),
          "unknown_inc": CM["n_unknown_inc"], "no_label": int(D.name.isna().sum()), "no_label_pct": pct(D.name.isna().sum(), N),
          "sea": len(sea), "inland": int((D.setting == "inland").sum()), "inland_pct": pct((D.setting == "inland").sum(), N),
          "countries": int(D[D.iso.notna()].iso.nunique()), "unassigned": int(D.iso.isna().sum()),
          "with_height": int(D.height_raw.notna().sum()), "with_focal": int(D.focal_raw.notna().sum()),
          "multi_year": int(D.year_all.fillna("").str.contains(r"\|").sum()),
          "sl0": int((D.sitelinks == 0).sum()), "sl0_pct": pct((D.sitelinks == 0).sum(), N),
          "sl_le1": int((D.sitelinks <= 1).sum()), "sl_le1_pct": pct((D.sitelinks <= 1).sum(), N),
          "with_article": int((D.sitelinks >= 1).sum()),
          "how": D.country_how.value_counts().to_dict(), "wd_country_mismatch": 0}
# location-based country against Wikidata's own country statement
mm = D[D.country_wd.notna() & D.iso.notna()]
cn = C["cname"]
alias = {"People's Republic of China": "China", "Russian Empire": "Russia", "Kingdom of the Netherlands": "Netherlands", "Kingdom of Denmark": "Denmark", "The Bahamas": "Bahamas"}
R["n"]["wd_country_mismatch"] = int(sum(1 for r in mm.itertuples() if r.country not in [alias.get(x, x) for x in r.country_wd.split("|")]))

# ---------------------------------------------------------------- by country
g = D[D.iso.notna()].groupby("iso")
bc = pd.DataFrame({"n": g.size(), "sea": g.apply(lambda x: int((x.setting == "sea").sum())), "inland": g.apply(lambda x: int((x.setting == "inland").sum())),
                   "dated": g.apply(lambda x: int(x.year.notna().sum())), "sl_le1": g.apply(lambda x: int((x.sitelinks <= 1).sum())),
                   "no_label": g.apply(lambda x: int(x["name"].isna().sum())), "oldest": g.year.min(),
                   "median_year": g.year.median()}).reset_index()
bc["name"] = bc.iso.map(lambda i: cn.get(i, i)); bc["coast_km"] = bc.iso.map(lambda i: C["coast_km"].get(i, 0.0))
bc["per1000"] = np.where(bc.coast_km > 0, 1000 * bc.sea / bc.coast_km.replace(0, np.nan), np.nan)
bc["sl_le1_pct"] = 100 * bc.sl_le1 / bc.n
bc = bc.sort_values("n", ascending=False).reset_index(drop=True)
out = bc[["iso", "name", "n", "sea", "inland", "dated", "coast_km", "per1000", "sl_le1", "sl_le1_pct", "no_label", "oldest", "median_year"]].copy()
out["per1000"] = out.per1000.round(2); out["sl_le1_pct"] = out.sl_le1_pct.round(1)
out.to_csv(f"{DATA}/by_country.csv", index=False)
row = lambda r: {"iso": r.iso, "name": r["name"], "n": int(r.n), "sea": int(r.sea), "inland": int(r.inland), "coast_km": round(float(r.coast_km)),
                 "per1000": None if pd.isna(r.per1000) else round(float(r.per1000), 1), "sl_le1_pct": round(float(r.sl_le1_pct), 1),
                 "dated": int(r.dated), "no_label": int(r.no_label)}
R["country"] = {"top": [row(r) for _, r in bc.head(25).iterrows()]}
top3 = bc.head(3)
R["country"]["top3_names"] = list(top3.name); R["country"]["top3_n"] = int(top3.n.sum()); R["country"]["top3_pct"] = pct(top3.n.sum(), N)
R["country"]["swe_pct"] = pct(int(bc[bc.iso == "SWE"].n.iloc[0]), N)
R["country"]["n_ge100"] = int((bc.n >= 100).sum())
R["country"]["n_coastal_countries"] = int(sum(1 for v in C["coast_km"].values() if v > 0))
R["country"]["coastal_with_none"] = sorted(cn[i] for i, v in C["coast_km"].items() if v >= 200 and i not in set(bc.iso))
R["country"]["world_coast_km"] = round(sum(C["coast_km"].values()))
R["country"]["world_per1000"] = round(1000 * len(sea) / sum(C["coast_km"].values()), 1)
dens = bc[(bc.coast_km >= 1000) & (bc.sea >= 10) & (bc.iso != "ATA")].sort_values("per1000", ascending=False)
R["country"]["dense_rule"] = "countries with at least 1,000 km of coast and 10 sea lights"
R["country"]["dense_n"] = len(dens)
R["country"]["dense"] = [row(r) for _, r in dens.head(25).iterrows()]
R["country"]["sparse"] = [row(r) for _, r in dens.tail(10).iloc[::-1].iterrows()]
R["country"]["by_iso"] = {r.iso: row(r) for _, r in bc.iterrows()}

# ---------------------------------------------------------------- coverage (how complete Wikidata is)
cov = bc[bc.n >= 40].sort_values("sl_le1_pct", ascending=False)
R["coverage"] = {"rule": "countries with at least 40 lighthouses", "most_bare": [row(r) for _, r in cov.head(8).iterrows()],
                 "least_bare": [row(r) for _, r in cov.tail(6).iloc[::-1].iterrows()],
                 "swe_no_label": int(bc[bc.iso == "SWE"].no_label.iloc[0]), "fin_no_label": int(bc[bc.iso == "FIN"].no_label.iloc[0]),
                 "fin_dated_pct": pct(int(bc[bc.iso == "FIN"].dated.iloc[0]), int(bc[bc.iso == "FIN"].n.iloc[0])),
                 "swe_dated_pct": pct(int(bc[bc.iso == "SWE"].dated.iloc[0]), int(bc[bc.iso == "SWE"].n.iloc[0]))}
by_cont = Counter()
for r in D.itertuples():
    cont = C["props"].get(r.iso, {}).get("cont", "Not assigned") if isinstance(r.iso, str) else "Not assigned"
    by_cont[{"Seven seas (open ocean)": "Islands of the open ocean"}.get(cont, cont)] += 1
R["coverage"]["by_continent"] = [{"name": k, "n": v, "pct": pct(v, N)} for k, v in by_cont.most_common()]
coast_cont = Counter()
for i, v in C["coast_km"].items():
    coast_cont[C["props"][i]["cont"]] += v
R["coverage"]["coast_by_continent"] = {k: round(v) for k, v in coast_cont.items()}

# ---------------------------------------------------------------- timeline
d = D[dated].copy(); d["dec"] = (d.year // 10 * 10).astype(int); d["cen"] = np.floor(d.year / 100).astype(int) + 1
GRP = [("SWE", "Sweden", "#2F6FB0"), ("USA", "United States", "#B3202A"), ("GBR", "United Kingdom", "#1E9E8E"),
       ("CAN", "Canada", "#E0662B"), ("FIN", "Finland", "#6B3FA0"), ("OTH", "Rest of the world", "#E3A21A")]
gk = [x[0] for x in GRP[:-1]]
d["grp"] = d.iso.where(d.iso.isin(gk), "OTH")
decs = list(range(1700, 2030, 10))
tl = {k: [int(((d.dec == y) & (d.grp == k)).sum()) for y in decs] for k, _, _ in GRP}
tot = [int((d.dec == y).sum()) for y in decs]
nos = [t - s for t, s in zip(tot, tl["SWE"])]
R["timeline"] = {"decades": decs, "groups": [[k, n, c] for k, n, c in GRP], "by_group": tl, "total": tot, "not_sweden": nos,
                 "before1700": int((d.year < 1700).sum()), "first_dec": 1700, "last_dec": 2020,
                 "peak_dec": decs[int(np.argmax(tot))], "peak_n": max(tot),
                 "peak_dec_nosw": decs[int(np.argmax(nos))], "peak_n_nosw": max(nos)}
ix = lambda y: decs.index(y)
T = R["timeline"]
T["c19"] = int(((d.year >= 1801) & (d.year <= 1900)).sum())   # strict centuries are awkward; use calendar 1800s below
T["n_from1700"] = int((d.year >= 1700).sum())
T["n1800s"] = int(((d.year >= 1800) & (d.year <= 1899)).sum()); T["n1900s"] = int(((d.year >= 1900) & (d.year <= 1999)).sum())
T["n1700s"] = int(((d.year >= 1700) & (d.year <= 1799)).sum()); T["n2000s"] = int((d.year >= 2000).sum())
ns = d[d.iso != "SWE"]
T["nosw_1800s"] = int(((ns.year >= 1800) & (ns.year <= 1899)).sum()); T["nosw_1900s"] = int(((ns.year >= 1900) & (ns.year <= 1999)).sum())
T["nosw_dated"] = len(ns)
T["nosw_1800s_x_1700s"] = round(T["nosw_1800s"] / max(1, int(((ns.year >= 1700) & (ns.year <= 1799)).sum())), 1)
T["nosw_1700s"] = int(((ns.year >= 1700) & (ns.year <= 1799)).sum())
T["nosw_1820s"] = nos[ix(1820)]; T["nosw_1870s"] = nos[ix(1870)]; T["nosw_1900s_dec"] = nos[ix(1900)]
T["nosw_1940s"] = nos[ix(1940)]; T["nosw_2010s"] = nos[ix(2010)]
T["nosw_1850_1909_avg"] = round(sum(nos[ix(1850):ix(1900) + 1]) / 6)
T["nosw_1970_2019_avg"] = round(sum(nos[ix(1970):ix(2010) + 1]) / 5)
T["nosw_drop_x"] = round(T["nosw_1850_1909_avg"] / T["nosw_1970_2019_avg"], 1)
sw = tl["SWE"]
T["swe_1930_1969"] = sum(sw[ix(1930):ix(1960) + 1]); T["swe_peak_dec"] = decs[int(np.argmax(sw))]; T["swe_peak_n"] = max(sw)
T["swe_share_1930_1969"] = pct(T["swe_1930_1969"], sum(tot[ix(1930):ix(1960) + 1]))
T["usa_peak_dec"] = decs[int(np.argmax(tl["USA"]))]; T["usa_peak_n"] = max(tl["USA"])
T["usa_1820_1909"] = sum(tl["USA"][ix(1820):ix(1900) + 1]); T["usa_after1950"] = sum(tl["USA"][ix(1950):])
T["gbr_peak_dec"] = decs[int(np.argmax(tl["GBR"]))]; T["gbr_peak_n"] = max(tl["GBR"])
T["all_1970_2019_avg"] = round(sum(tot[ix(1970):ix(2010) + 1]) / 5); T["all_1900s_dec"] = tot[ix(1900)]
T["all_2010s"] = tot[ix(2010)]; T["all_2020s"] = tot[ix(2020)]
hmax = D.height_raw.map(lambda s: max(float(x) for x in s.split("|")) if isinstance(s, str) else np.nan)
sw3069 = (D.iso == "SWE") & D.year.between(1930, 1969); old5009 = (D.iso != "SWE") & D.year.between(1850, 1909)
T["swe_3069_h_median"] = round(float(hmax[sw3069].median()), 1); T["swe_3069_h_n"] = int(hmax[sw3069].notna().sum())
T["nosw_5009_h_median"] = round(float(hmax[old5009].median()), 1); T["nosw_5009_h_n"] = int(hmax[old5009].notna().sum())
T["swe_3069_sl0_pct"] = pct(int(((D.sitelinks == 0) & sw3069).sum()), int(sw3069.sum()))
pd.DataFrame({"decade": decs, **{n: tl[k] for k, n, _ in GRP}, "total": tot, "total_without_sweden": nos}).to_csv(f"{DATA}/by_decade.csv", index=False)
cen = Counter(d.cen)
R["timeline"]["by_century"] = [{"c": int(k), "n": int(cen[k])} for k in sorted(cen)]

# ---------------------------------------------------------------- oldest
# Whether a tower still stands is not in the Wikidata extract. For the oldest dated items I marked it by hand from their
# well documented histories (see the paper); "not checked" where I could not be sure.
STATUS = {
    "Q43244": ("Lost", "Fell to earthquakes in the Middle Ages; nothing stands"),
    "Q131824651": ("Lost", "Known from ancient writers; the tower is gone"),
    "Q245151": ("Standing", "Roman tower, refaced in the 1700s; still lit"),
    "Q3715786": ("Standing", "Roman tower inside Dover Castle, a ruin"),
    "Q848397": ("Rebuilt", "Tower on the islet rebuilt several times since"),
    "Q5897891": ("Standing", "Medieval tower, still lit; the year is Wikidata's and looks rounded to a century"),
    "Q5856454": ("Standing", "Still lit, at the port of Palma"),
    "Q12728147": ("Rebuilt", "Wikidata's date is the Genoese era it commemorates; the tower is from 1860"),
    "Q1821443": ("Standing", "Medieval tower on Neuwerk island"),
    "Q3378334": ("Rebuilt", "The present tower is from 1959 (Wikipedia list of tallest lighthouses)"),
    "Q7587435": ("Standing", "Medieval oratory tower on St Catherine's Down, Isle of Wight"),
    "Q3533595": ("Standing", "Tower at the harbour of La Rochelle"),
    "Q1409002": ("Standing", "Fortress tower at the mouth of the Vistula, Gdańsk"),
    "Q1795607": ("Standing", "Still lit, on Hiiumaa"),
    "Q1821461": ("Standing", "Old tower, now a museum"),
    "Q776666": ("Standing", "Rebuilt in 1543 and still lit (Wikipedia list of tallest lighthouses)"),
    "Q199234": ("Standing", "Still lit, in the Gironde estuary"),
}
o = D[dated].sort_values(["year", "sitelinks"], ascending=[True, False]).head(32)
R["oldest"] = [{"qid": r.qid, "name": r["name"] if isinstance(r["name"], str) else f"No English label ({r.qid})", "year": int(r.year),
                "country": r.country, "lat": round(r.lat, 4), "lon": round(r.lon, 4), "sitelinks": int(r.sitelinks),
                "status": STATUS.get(r.qid, ("Not checked", ""))[0], "note": STATUS.get(r.qid, ("", ""))[1]} for _, r in o.iterrows()]
st = [x for x in R["oldest"] if x["status"] == "Standing"]
R["oldest_standing"] = st[:10]
OL = {x["name"]: x for x in R["oldest"]}
R["spot"] = {k: OL[k] for k in ("Lighthouse of Alexandria", "Tower of Hercules", "Dubris Pharos", "Hook Lighthouse", "Kõpu Lighthouse", "Lighthouse of Genoa", "Cordouan Lighthouse")}
R["n"]["before1500"] = int((D.year < 1500).sum()); R["n"]["before1800"] = int((D.year < 1800).sum())
R["n"]["oldest_checked"] = len(STATUS)

# ---------------------------------------------------------------- tallest (Wikipedia list, metres from the list)
W = jload(f"{RAW}/wiki_List_of_tallest_lighthouses.json")
tb = pd.read_html(io.StringIO(W["html"]))[0]
ALIAS = {"Phare de Gatteville": "new Gatteville Lighthouse", "Borkum Großer Light": "Borkum Großer Leuchtturm"}
WCN = {"China": "China", "Russia": "Russia"}
tall = []
for _, r in tb.iterrows():
    m = re.search(r"(\d+)\s*feet\s*\((\d+)", str(r.Height))
    nm = str(r.Name).strip(); ctry = str(r.Country).strip()
    cand = D[D.name.notna() & (D.country == ctry)]
    key = norm(ALIAS.get(nm, nm))
    k2 = re.sub(r"^(phare de |phare d |lighthouse of )|( lighthouse| light)$", "", key)
    hit = cand[cand.name.map(lambda s: norm(s) == key or k2 in norm(s))].sort_values("sitelinks", ascending=False)   # best known item, not an older tower on the site
    h = hit.iloc[0] if len(hit) else None
    wh = None if h is None or not isinstance(h.height_raw, str) else [float(x) for x in h.height_raw.split("|")]
    tall.append({"rank": int(r.Order), "name": nm, "ft": int(m.group(1)), "m": int(m.group(2)), "country": ctry,
                 "place": str(r.Location).strip(), "year": str(r.Year).strip(), "build": str(r.Construction).strip(),
                 "remark": "" if pd.isna(r.Remarks) else str(r.Remarks).strip(),
                 "qid": None if h is None else h.qid, "lat": None if h is None else round(h.lat, 4), "lon": None if h is None else round(h.lon, 4),
                 "wd_height": wh})
R["tallest"] = {"rows": tall, "n": len(tall), "revid": int(W["revid"]), "matched": sum(1 for t in tall if t["qid"])}
unit = Counter()
for t in tall:
    if not t["wd_height"]:
        unit["none"] += 1; continue
    v = max(t["wd_height"])
    unit["metres" if abs(v - t["m"]) <= 3 else "feet" if abs(v - t["ft"]) <= 6 else "other"] += 1
R["tallest"]["wd_unit"] = dict(unit)
R["tallest"]["by_country"] = Counter(t["country"] for t in tall).most_common()
R["tallest"]["n_before1900"] = sum(1 for t in tall if re.match(r"1[0-8]\d\d", t["year"]))
R["tallest"]["stone_or_brick"] = sum(1 for t in tall if re.search(r"stone|granite|brick", t["build"], re.I))
R["tallest"]["top"] = tall[0]
pd.DataFrame(tall).drop(columns=["wd_height"]).to_csv(f"{DATA}/tallest_wikipedia.csv", index=False)
# Wikidata heights: amounts only (unit lost), so only an honest summary
hv = D.height_raw.dropna().map(lambda s: max(float(x) for x in s.split("|")))
R["heights"] = {"n": int(len(hv)), "median": round(float(hv.median()), 1), "n_over_70": int((hv > 70).sum()),
                "over_70": [{"name": r["name"], "v": float(max(float(x) for x in r.height_raw.split("|")))} for _, r in D[D.height_raw.notna()].iterrows()
                            if max(float(x) for x in r.height_raw.split("|")) > 70 and isinstance(r["name"], str)][:0]}
cg_ = D[D.name.isin(["Lighthouse of La Coubre", "Cape Hatteras Lighthouse"])]
R["heights"]["examples"] = {r["name"]: r.height_raw for _, r in cg_.iterrows()}

# ---------------------------------------------------------------- densest coasts (first-level regions)
reg = pd.DataFrame(RG["regions"])
rc = sea.groupby("region_id").size().rename("sea")
reg = reg.merge(rc, left_on="id", right_index=True, how="left").fillna({"sea": 0})
reg["country"] = reg.iso.map(lambda i: cn.get(i, i))
reg["per100"] = np.where(reg.coast_km > 0, 100 * reg.sea / reg.coast_km.replace(0, np.nan), np.nan)
rr = reg[(reg.coast_km >= 150) & (reg.sea >= 15)].sort_values("per100", ascending=False)
REGFIX = {"Stockholm": "Stockholm County", "Västra Götaland": "Västra Götaland", "Uusimaa": "Uusimaa"}
R["regions"] = {"rule": "regions with at least 150 km of coast and 15 sea lights", "n": int(len(rr)),
                "top": [{"id": r.id, "name": r["name"], "country": r.country, "iso": r.iso, "sea": int(r.sea), "coast_km": round(float(r.coast_km)),
                         "per100": round(float(r.per100), 1)} for _, r in rr.head(20).iterrows()],
                "most": [{"id": r.id, "name": r["name"], "country": r.country, "sea": int(r.sea), "coast_km": round(float(r.coast_km))}
                         for _, r in reg.sort_values("sea", ascending=False).head(10).iterrows()]}
reg[reg.coast_km > 0][["id", "name", "country", "iso", "type", "coast_km", "sea", "per100"]].round({"per100": 2}).sort_values("per100", ascending=False).to_csv(f"{DATA}/regions_coast.csv", index=False)
# regions outside Sweden and Finland, so the headline is not only Sweden and Finland
R["regions"]["top_outside_nordic"] = [x for x in R["regions"]["top"] if x["iso"] not in ("SWE", "FIN")][:8]

# ---------------------------------------------------------------- page data
P = []
for r in D.itertuples():
    P.append([round(r.lat, 4), round(r.lon, 4), None if pd.isna(r.year) else int(r.year), int(r.era), r.name if isinstance(r.name, str) else "",
              r.country, r.qid, int(r.sitelinks), r.height_raw if isinstance(r.height_raw, str) else "",
              r.focal_raw if isinstance(r.focal_raw, str) else "", 1 if r.setting == "inland" else 0, r.year_all if isinstance(r.year_all, str) else ""])
jsave({"cols": ["lat", "lon", "year", "era", "name", "country", "qid", "sitelinks", "height_raw", "focal_raw", "inland", "years"], "rows": P}, f"{DATA}/points.json")
SITE = {"eras": [list(e) for e in ERAS], "groups": R["timeline"]["groups"], "cpos": jload(f"{WORK}/cpos.json"),
        "tall_m": {t["qid"]: t["m"] for t in tall if t["qid"]}, "status": {k: list(v) for k, v in STATUS.items()},
        "regpts": {r["id"]: [int(i) for i in D.index[(D.region_id == r["id"]) & (D.setting == "sea")]] for r in R["regions"]["top"] + R["regions"]["top_outside_nordic"]}}
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)

# quick look
print(json.dumps(R["n"], indent=0)[:900])
print("top", [(c["name"], c["n"]) for c in R["country"]["top"][:10]])
print("dense", [(c["name"], c["per1000"], c["sea"], c["coast_km"]) for c in R["country"]["dense"][:12]])
print("sparse", [(c["name"], c["per1000"], c["sea"], c["coast_km"]) for c in R["country"]["sparse"]])
print("regions", [(c["name"], c["country"], c["per100"], c["sea"], c["coast_km"]) for c in R["regions"]["top"][:14]])
print("reg non-nordic", [(c["name"], c["country"], c["per100"]) for c in R["regions"]["top_outside_nordic"]])
print("tall", R["tallest"]["matched"], R["tallest"]["wd_unit"], [(t["name"], t["qid"], t["wd_height"], t["m"]) for t in tall])
print({k: v for k, v in T.items() if not isinstance(v, (list, dict))})
print("cont", R["coverage"]["by_continent"])
print("bare", [(c["name"], c["sl_le1_pct"]) for c in R["coverage"]["most_bare"]], [(c["name"], c["sl_le1_pct"]) for c in R["coverage"]["least_bare"]])
print("coastal none", R["country"]["coastal_with_none"])
