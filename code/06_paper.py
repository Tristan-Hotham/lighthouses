"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays a placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Lighthouses_of_the_World"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# checks for statements made in words in the paper only
assert R["regions"]["top_outside_nordic"][2]["country"] == "Tunisia"
assert R["coverage"]["least_bare"][0]["name"] == "Estonia"
assert all(R["country"]["by_iso"][i]["sl_le1_pct"] > 90 for i in ("SWE", "FIN", "MDG"))
assert R["coverage"]["fin_dated_pct"] < 20 < 90 < R["coverage"]["swe_dated_pct"]
assert R["oldest"][1]["name"] == "Tower of Caepio" and R["oldest"][1]["status"] == "Lost"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return fmt(v, "yr").replace(" ", "~")
    return tex(str(v))


yr = lambda y: fmt(y, "yr").replace(" ", "~")
rows = "".join(f"{tex(c['name'])} & {c['n']:,} & {c['inland']:,} & {c['coast_km']:,} & {'' if c['per1000'] is None else format(c['per1000'], '.1f')} & {c['sl_le1_pct']:.0f}\\%\\\\\n" for c in R["country"]["top"][:20])
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty countries with most lighthouses in Wikidata. Inland: lake and river lights. Coast: Natural Earth 1:10m. Bare: share with at most one Wikipedia article.}\\label{tab:countries}"
      "\\begin{tabular}{lrrrrr}\\toprule Country & Lights & Inland & Coast km & Sea lights per 1,000 km & Bare\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(r['name'])} & {tex(r['country'])} & {r['sea']:,} & {r['coast_km']:,} & {r['per100']:.1f}\\\\\n" for r in R["regions"]["top"])
TR = ("\\begin{table}[tbp]\\centering\\small\\caption{The densest regional coasts: sea lights per 100~km, " + tex(R["regions"]["rule"]) + ".}\\label{tab:regions}"
      "\\begin{tabular}{llrrr}\\toprule Region & Country & Sea lights & Coast km & Per 100 km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{yr(o['year'])} & {tex(o['name'])} & {tex(o['country'])} & {tex(o['status'])} & {tex(o['note'])}\\\\\n" for o in R["oldest"][:24])
TO = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The oldest dated lighthouses in Wikidata (inception year), with their status today where checked by hand.}\\label{tab:oldest}"
      "\\begin{tabular}{rp{3.8cm}p{2.4cm}lp{5.0cm}}\\toprule Year & Lighthouse & Country & Today & Note\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("COUNTRIES", TC), ("REGIONS", TR), ("OLDEST", TO)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:3]
t = t.replace("@@DOILINK@@", "https://doi.org/\\{\\{DOI\\}\\}")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
