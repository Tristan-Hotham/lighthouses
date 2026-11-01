"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json is loaded by the page.
Facts stated in words (page, blog, paper, collage) are checked here. The full-screen map snippet is pasted before </body>."""
import json
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
T, CO, RG = R["timeline"], R["country"], R["regions"]
B = CO["by_iso"]

# ---- facts stated in words (page, blog, paper, collage)
assert [c["iso"] for c in CO["top"][:5]] == ["SWE", "USA", "FIN", "CAN", "GBR"], [c["iso"] for c in CO["top"][:5]]
assert [c["iso"] for c in CO["dense"][:4]] == ["SWE", "FIN", "TUN", "DEU"]
assert B["TUN"]["sl_le1_pct"] > 80 and B["SWE"]["sl_le1_pct"] > 90 and B["FIN"]["sl_le1_pct"] > 90 and B["USA"]["sl_le1_pct"] < 20
assert 35 <= B["GBR"]["per1000"] < B["ESP"]["per1000"] < B["FRA"]["per1000"] < 50                     # "sit together a little lower"
assert B["CAN"]["per1000"] < 5 and B["RUS"]["per1000"] < 5 and B["IDN"]["per1000"] < 1
assert {"Greenland", "Nigeria", "Kenya", "Ecuador", "United Arab Emirates"} <= set(CO["coastal_with_none"])
assert all(r["iso"] in ("SWE", "FIN") for r in RG["top"][:10]) and RG["top"][0]["name"] == "Västra Götaland"
assert [r["name"] for r in RG["top_outside_nordic"][:2]] == ["Lower Saxony", "Connecticut"]
nos = dict(zip(T["decades"], T["not_sweden"]))
assert T["peak_dec_nosw"] == 1870 and all(nos[d] > 300 for d in range(1850, 1910, 10)) and nos[1910] < 300   # "above three hundred a decade until the First World War"
assert T["usa_peak_dec"] == 1870 and T["swe_peak_dec"] == 1940 and T["peak_dec"] == 1900
assert T["swe_3069_h_median"] < T["nosw_5009_h_median"]
assert R["tallest"]["top"]["name"] == "Île Vierge Lighthouse" and R["tallest"]["wd_unit"]["feet"] == 1
ft = [t for t in R["tallest"]["rows"] if t["wd_height"] and abs(max(t["wd_height"]) - t["ft"]) <= 6]
assert len(ft) == 1 and ft[0]["name"] == "Cape Hatteras Light" and max(ft[0]["wd_height"]) == 210
assert all(t["m"] >= 60 for t in R["tallest"]["rows"])
OS = [o["name"] for o in R["oldest_standing"]]
assert OS[:2] == ["Tower of Hercules", "Dubris Pharos"] and R["oldest"][0]["name"] == "Lighthouse of Alexandria" and R["oldest"][0]["status"] == "Lost"
assert [o["name"] for o in R["oldest"] if o["year"] < R["spot"]["Tower of Hercules"]["year"]] == ["Lighthouse of Alexandria", "Tower of Caepio"]
OLD = {o["name"]: o for o in R["oldest"]}
assert OLD["Planier Light"]["year"] == 1326 and OLD["Genoese Lighthouse"]["year"] == 1300
assert any(t["name"] == "Planier Light" and t["year"] == "1959" for t in R["tallest"]["rows"])
bc = {c["name"]: c for c in R["coverage"]["by_continent"]}
assert [c["name"] for c in R["coverage"]["by_continent"][:5]] == ["Europe", "North America", "Asia", "Africa", "South America"]
D = pd.read_csv(f"{DATA}/lighthouses.csv", dtype=str)
inl = D[D.setting == "inland"].country.value_counts()
assert list(inl.index[:3]) == ["Sweden", "United States", "Finland"]                                   # "mostly Great Lakes and Swedish and Finnish lakes"


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23857614", "https://blog.tristanhotham.com/2026/10/31/lighthouses/"}, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
