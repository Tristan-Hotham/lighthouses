"""Reddit collage (r/dataisbeautiful style): light paper, a world map of every lighthouse coloured by when it was built,
a night-glow inset of northern Europe, lights built per decade, and three small panels. Every number from results.json.
Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from figstyle import *
import importlib.util
spec = importlib.util.spec_from_file_location("figs", os.path.join(ROOT, "code", "05_figures.py")); F = importlib.util.module_from_spec(spec); spec.loader.exec_module(F)

R = jload(f"{DATA}/results.json"); D = lights()
T, CO, N = R["timeline"], R["country"], R["n"]
HALO = [pe.withStroke(linewidth=4.5, foreground=BG)]
OUT = os.path.join(ROOT, "reddit", "lighthouses_of_the_world.png")

fig = plt.figure(figsize=(16, 21.6), dpi=150, facecolor=BG)
# ---------------------------------------------------------------- title
fig.text(.045, .968, "Every lighthouse in the world", fontproperties=DISP, fontsize=54, color=FG, va="center")
fig.text(.045, .938, f"{N['items']:,} lighthouses with a place in Wikidata, coloured by when they were built or first lit. Outside Sweden, building",
         fontproperties=SERP, fontsize=17, color=FG, va="center")
fig.text(.045, .923, f"peaked in the {T['peak_dec_nosw']}s; Sweden's own register, loaded light by light, adds a second wave of small lights in the 1930s to 1960s.",
         fontproperties=SERP, fontsize=17, color=FG, va="center")

# ---------------------------------------------------------------- world map (light)
ax = fig.add_axes([.02, .585, .96, .325]); outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, lw=.25)
X, Y = proj(D.lon, D.lat)
dd = D.assign(x=X, y=Y)
und = dd[dd.year.isna()]; ax.scatter(und.x, und.y, s=2.6, c=ECOL[-1], lw=0, alpha=.75, zorder=3)
dt = dd[dd.year.notna()].sort_values("year", ascending=False)
ax.scatter(dt.x, dt.y, s=4.2, c=[ECOL[e] for e in dt.era], lw=0, alpha=.9, zorder=4)
old = dd[dd.year < 1700]; ax.scatter(old.x, old.y, s=26, c=ECOL[0], lw=.8, edgecolor="white", zorder=6)


from shapely.geometry import shape, box as sbox
from shapely.ops import unary_union, transform as stransform
LANDG = unary_union([shape(f["geometry"]).buffer(0) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]])
LANDG = stransform(lambda x, y, z=None: EE.transform(np.clip(x, -179.99, 179.99), np.clip(y, -89.9, 89.9)), LANDG).buffer(25000)   # 25 km margin
from shapely.geometry import MultiPoint
PTS = MultiPoint(list(zip(X, Y))).buffer(25000)                                                                  # the lights themselves
CLEAR = LANDG.union(PTS)


def text_boxes(arts):
    fig.canvas.draw(); inv = ax.transData.inverted(); r = fig.canvas.get_renderer()
    out = []
    for t in arts:
        e = t.get_window_extent(renderer=r); (x0, y0), (x1, y1) = inv.transform([(e.x0, e.y0), (e.x1, e.y1)])
        out.append(sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    return out


PLACED = []


def callout(lon, lat, cands, text, ha="center", col=FG, big=None):
    """Try each candidate label position (lon, lat of the label, lon, lat where the leader ends) in turn and keep the
    first whose text boxes clear land (Natural Earth 1:50m, 25 km margin), every lighthouse and earlier labels."""
    px, py = proj(lon, lat)
    for tlon, tlat, elon, elat in cands:
        tx, ty = proj(tlon, tlat); ex, ey = proj(elon, elat)
        arts = [ax.text(tx, ty, big, fontproperties=DISP, fontsize=22, color=col, ha=ha, va="bottom", zorder=9, path_effects=HALO),
                ax.text(tx, ty - 1.2e5, text, fontsize=11, color=FG, ha=ha, va="top", zorder=9, path_effects=HALO, linespacing=1.3)]
        bx = text_boxes(arts)
        if not any(b.intersects(CLEAR) or any(b.intersects(q) for q in PLACED) for b in bx):
            PLACED.extend(bx)
            from shapely.geometry import Point, LineString
            from shapely.ops import nearest_points
            lab = unary_union(bx).buffer(60000)                      # leader stops 60 km short of the text
            ex, ey = nearest_points(lab.boundary, Point(px, py))[0].coords[0]
            leader = LineString([(px, py), (ex, ey)])
            assert not any(leader.intersects(q) for q in PLACED), "leader crosses a label"
            ax.plot([px, ex], [py, ey], color=MUT, lw=1.0, zorder=7, solid_capstyle="round")
            ax.scatter([px], [py], s=46, facecolor="none", edgecolor=FG, lw=1.4, zorder=8)
            print("label", text.split(chr(10))[0], "at", tlon, tlat)
            return
        for b_ in bx:
            g_ = b_.intersection(CLEAR)
            if not g_.is_empty:
                c_ = g_.centroid; print("   box", [round(v / 1e3) for v in b_.bounds], "hits near", [round(v, 1) for v in EE.transform(c_.x, c_.y, direction="INVERSE")], "land" if b_.intersects(LANDG) else "lights")
        print("  rejected", tlon, tlat, ["land/lights" if b.intersects(CLEAR) else "label" for b in bx if b.intersects(CLEAR) or any(b.intersects(q) for q in PLACED)])
        for t in arts:
            t.remove()
    raise SystemExit(f"no clear position for label: {text}")


TH = R["spot"]["Tower of Hercules"]; IV = R["tallest"]["top"]; IDN = CO["by_iso"]["IDN"]; SW = CO["by_iso"]["SWE"]
US = CO["by_iso"]["USA"]
callout(-76.3, 37.5, [(-40, 25, -46, 27.5), (-42, 22, -47, 25), (-38, 20, -44, 23), (-44, 30, -50, 32), (-46, 33, -52, 34), (-40, 30, -46, 32), (-36, 26, -42, 28), (-34, 22, -40, 25)], f"US lights,\n{US['inland']} on lakes\nand rivers", col=HOT, big=f"{US['n']:,}")
callout(3.4, 6.4, [(-20, -24, -15, -20.5), (-24, -26, -18, -22), (-26, -30, -20, -26), (-14, -32, -10, -28)], "Nigeria: no\nlighthouse in\nWikidata at all", col=MUT, big="None")
callout(112, -7.2, [(84, -31, 92, -28.2), (82, -34, 90, -31)], f"Indonesia: {IDN['n']} lights\non {IDN['coast_km']:,} km of coast", col=MUT, big="Dark coasts")
H = [Line2D([], [], ls="", marker="o", ms=10, mfc=e[1], mec="none", label=("Built " + e[0][0].lower() + e[0][1:]) if i < len(ERAS) - 1 else "Date not recorded") for i, e in enumerate(ERAS)]
ax.legend(handles=H, loc="lower center", bbox_to_anchor=(.5, -.075), ncol=7, frameon=False, fontsize=11.5, handletextpad=.25, columnspacing=1.3)

# ---------------------------------------------------------------- timeline
fig.text(.045, .535, "Lighthouses built per decade", fontproperties=DISPB, fontsize=23, color=FG, va="center")
fig.text(.045, .518, f"{T['n_from1700']:,} lighthouses dated 1700 or later. The 2020s are only part way through.", fontsize=11.5, color=MUT, va="center")
a2 = fig.add_axes([.065, .325, .55, .18]); a2.set_facecolor(BG)
decs = np.array(T["decades"]); bot = np.zeros(len(decs))
for k, n, c in T["groups"]:
    v = np.array(T["by_group"][k]); a2.bar(decs, v, bottom=bot, width=8.6, color=c, lw=0, label=n); bot += v
spines(a2); a2.set_xlim(1695, 2030); a2.set_ylim(0, 640); a2.tick_params(labelsize=11)
a2.text(1702, 610, f"Outside Sweden: {T['nosw_1820s']} new lights in the 1820s,\n{T['peak_n_nosw']} in the {T['peak_dec_nosw']}s (the peak), {T['nosw_2010s']} in the 2010s",
        fontsize=12, color=FG, va="top", linespacing=1.45)
a2.annotate(f"{T['all_1900s_dec']} in the 1900s", (1904, T["all_1900s_dec"] + 4), (1916, 575), fontsize=11.5, ha="left", color=FG,
            arrowprops=dict(arrowstyle="-", color=MUT, lw=.9))
a2.text(1972, 455, f"Sweden: {T['swe_peak_n']}\nin the {T['swe_peak_dec']}s", fontsize=11.5, color=COOL, ha="left", va="bottom", fontweight="medium")
a2.legend(frameon=False, fontsize=11, loc="upper left", bbox_to_anchor=(0, .74), ncol=1, handlelength=1.1)

# ---------------------------------------------------------------- night inset
fig.text(.655, .535, "Northern Europe at night", fontproperties=DISPB, fontsize=23, color=FG, va="center")
fig.text(.655, .518, "One small glow per lighthouse", fontsize=11.5, color=MUT, va="center")
bx = fig.add_axes([.655, .295, .3, .21])
F.night_neu(bx, ext=(-1.45e6, 1.25e6, -1.25e6, 1.3e6), gain=.5, px=(900, 850))
bx.add_patch(Rectangle((0, 0), 1, 1, transform=bx.transAxes, fc="none", ec=FG, lw=1.6, zorder=20))
bx.text(.03, .965, f"Sweden: {SW['n']:,} lights,\n{SW['per1000']:.0f} per 1,000 km\nof coast (world {CO['world_per1000']:.1f})", transform=bx.transAxes, fontsize=11, color="#FFE2A6", zorder=21, va="top", linespacing=1.35)

# ---------------------------------------------------------------- three small panels
def head(x, t, s):
    fig.text(x, .262, t, fontproperties=DISPB, fontsize=20, color=FG, va="center")
    fig.text(x, .246, s, fontsize=11, color=MUT, va="center")


head(.045, "Most lights per 1,000 km of coast", "Sea lights; countries with 1,000 km of coast or more")
c1 = fig.add_axes([.165, .07, .17, .165]); c1.set_facecolor(BG)
den = CO["dense"][:10]
c1.barh(range(10), [c["per1000"] for c in den], color=LAMP); c1.invert_yaxis(); c1.set_yticks(range(10)); c1.set_yticklabels([c["name"] for c in den], fontsize=11.5)
for i, c in enumerate(den): c1.text(c["per1000"] + 6, i, f"{c['per1000']:.0f}", va="center", fontsize=11, color=FG)
c1.set_xlim(0, 400); c1.set_xticks([]); spines(c1); c1.spines["bottom"].set_visible(False)

head(.385, "The tallest", "Tower height, Wikipedia's List of tallest lighthouses")
c2 = fig.add_axes([.53, .07, .12, .165]); c2.set_facecolor(BG)
tl = R["tallest"]["rows"][:10]
c2.barh(range(10), [t["m"] for t in tl], color=[INK if re.search(r"stone|granite|brick", t["build"], re.I) else COOL for t in tl]); c2.invert_yaxis()
c2.set_yticks(range(10)); c2.set_yticklabels([f"{t['name'].replace(' Lighthouse', '').replace(' lighthouse', '').replace(' Light', '').replace('Lighthouse of ', '')}, {t['year']}" for t in tl], fontsize=11)
for i, t in enumerate(tl): c2.text(t["m"] + 2, i, f"{t['m']} m", va="center", fontsize=11, color=FG)
c2.set_xlim(0, 100); c2.set_xticks([]); spines(c2); c2.spines["bottom"].set_visible(False)
c2.legend(handles=[Rectangle((0, 0), 1, 1, color=INK, label="stone or brick"), Rectangle((0, 0), 1, 1, color=COOL, label="concrete or steel")], frameon=False, fontsize=10.5, loc="lower right", bbox_to_anchor=(1.3, -.11), ncol=2, handlelength=1)

head(.715, "Oldest still standing", "Year from Wikidata, in date order; standing\nchecked by hand")
y = .224
for o in R["oldest_standing"][:8]:
    fig.text(.715, y, fmt(o["year"], "yr"), fontsize=14, fontweight="medium", color=HOT, va="center")   # Plex Mono: Fraunces Black 3s read as 5s
    fig.text(.79, y, f"{o['name']}", fontsize=11.5, color=FG, va="center")
    fig.text(.79, y - .0095, o["country"] + (", tower medieval, year rounded" if o["qid"] == "Q5897891" else ""), fontsize=10, color=MUT, va="center")
    y -= .0205
fig.text(.715, y - .001, f"Gone: the Pharos of Alexandria, {fmt(R['spot']['Lighthouse of Alexandria']['year'], 'yr')}", fontsize=10.5, color=MUT, va="center")

# ---------------------------------------------------------------- footer
fig.add_artist(Line2D([.045, .955], [.047, .047], color=FG, lw=1.2))
fig.text(.045, .036, "Sources: Wikidata (CC0), lighthouses and their subclasses with coordinates, via QLever; Wikipedia contributors, List of tallest", fontsize=10.5, color=MUT, va="center")
fig.text(.045, .025, "lighthouses (CC BY-SA 4.0); Natural Earth (coasts measured at 1:10m). Wikidata coverage varies by country: some national lists", fontsize=10.5, color=MUT, va="center")
fig.text(.045, .014, "are loaded in full (Sweden, Finland), others barely appear. Dates are the first light on the site as Wikidata gives it.", fontsize=10.5, color=MUT, va="center")
fig.text(.045, .004, "Analysis and chart: Tristan Hotham, with Python and matplotlib", fontsize=10.5, color=MUT, va="center")
fig.text(.955, .004, "maps.tristanhotham.com/lighthouses", fontsize=12, color=FG, va="center", ha="right", fontweight="medium")
fig.savefig(OUT, dpi=150, facecolor=BG)
from PIL import Image
print(OUT, Image.open(OUT).size)
