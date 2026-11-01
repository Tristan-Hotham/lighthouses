"""Header card (header.png), blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json")
D = lights()
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
T, CO = R["timeline"], R["country"]
X, Y = proj(D.lon, D.lat)
NEU = (-12, 47, 32, 67.5)        # northern Europe close-up, lon/lat box
LAEA = Transformer.from_crs(4326, "+proj=laea +lat_0=57 +lon_0=12 +datum=WGS84", always_xy=True)


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def night_world(ax, gain=.9):
    outline(ax, fc=NSEA, ec=NEDGE, lw=.6)
    world(ax, lw=.25, land=NLAND, ec=NEDGE)
    glow(ax, X, Y, WORLD_EXT, px=(2000, 1025), sig=(1.0, 4.0), gain=gain)


def night_neu(ax, ext=None, gain=.5, px=(1400, 1400)):
    xs, ys = proj([NEU[0], NEU[2], NEU[0], NEU[2], 12, 12], [NEU[1], NEU[1], NEU[3], NEU[3], NEU[1], NEU[3]], LAEA)
    ext = ext or (-1.25e6, 1.25e6, -1.05e6, 1.2e6)
    ax.add_patch(Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fc=NSEA, ec="none", zorder=0))
    G = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
    for f in G["features"]:
        for ring in rings(f["geometry"]):
            if ring[:, 0].max() < -30 or ring[:, 0].min() > 50 or ring[:, 1].max() < 40:
                continue
            x, y = LAEA.transform(ring[:, 0], ring[:, 1])
            ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=NLAND, ec=NEDGE, lw=.3, zorder=1))
    x, y = LAEA.transform(D.lon.values, D.lat.values)
    glow(ax, x, y, ext, px=px, sig=(1.0, 3.5), gain=gain)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
    return ext


if __name__ == "__main__":
    # 1. night world map
    fig = plt.figure(figsize=(13, 7.4), facecolor=NSEA)
    ax = fig.add_axes([.01, .02, .98, .86]); night_world(ax)
    fig.text(.02, .955, f"Every lighthouse in Wikidata, {R['n']['items']:,} of them, lit up", fontproperties=DISPB, fontsize=20, color="#FFE2A6", va="center")
    fig.text(.02, .905, "Each light is a small glow; where they crowd, the coast shines. Equal Earth projection.", fontsize=11, color="#AFC0D6", va="center")
    both(fig, "glow_world")

    # 2. northern Europe close-up at night
    fig = plt.figure(figsize=(10, 9.4), facecolor=NSEA)
    ax = fig.add_axes([0, 0, 1, .92]); night_neu(ax)
    fig.text(.03, .955, "Northern Europe at night: the Swedish and Finnish skerries outshine everything", fontproperties=DISPB, fontsize=15.5, color="#FFE2A6", va="center")
    both(fig, "glow_north")

    # 3. timeline
    fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG); ax.set_facecolor(BG)
    decs = np.array(T["decades"]); bot = np.zeros(len(decs))
    for k, n, c in T["groups"]:
        v = np.array(T["by_group"][k]); ax.bar(decs, v, bottom=bot, width=8.6, color=c, lw=0, label=n); bot += v
    spines(ax); ax.set_xlim(1695, 2030); ax.set_ylim(0, 560)
    ax.set_ylabel("lighthouses built per decade", fontsize=10.5)
    ax.annotate(f"{T['all_1900s_dec']} in the 1900s", (1900, T["all_1900s_dec"]), (1880, 535), fontsize=10, ha="center", color=FG)
    ax.text(1955, 470, f"Sweden's register:\n{T['swe_peak_n']} in the {T['swe_peak_dec']}s", fontsize=10, ha="center", color=COOL)
    ax.text(1712, 150, f"Outside Sweden, new lights peak\nin the {T['peak_dec_nosw']}s ({T['peak_n_nosw']}) and fall\n{T['nosw_drop_x']:.1f} times by 1970 to 2019", fontsize=10.5, color=FG, va="top")
    ax.legend(frameon=False, fontsize=10, loc="upper left", ncol=3, bbox_to_anchor=(0, 1.0))
    ax.set_title(f"{T['n_from1700']:,} lighthouses dated 1700 or later, by the decade Wikidata gives for their building or first light", loc="left", fontsize=12, color=FG, pad=26)
    fig.tight_layout(); both(fig, "timeline")

    # 4. countries: number and per 1,000 km of coast
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 6.4), facecolor=BG)
    top = CO["top"][:15]; den = CO["dense"][:15]
    a1.barh(range(15), [c["n"] for c in top], color=INK); a1.barh(range(15), [c["inland"] for c in top], color=COOL)
    a1.set_yticks(range(15)); a1.set_yticklabels([c["name"] for c in top], fontsize=10); a1.invert_yaxis()
    for i, c in enumerate(top): a1.text(c["n"] + 30, i, f"{c['n']:,}", va="center", fontsize=9.5, color=MUT)
    a1.set_title("Lighthouses (blue: on lakes and rivers)", loc="left", fontsize=11.5); spines(a1); a1.set_xlim(0, top[0]["n"] * 1.15)
    a2.barh(range(15), [c["per1000"] for c in den], color=LAMP)
    a2.set_yticks(range(15)); a2.set_yticklabels([c["name"] for c in den], fontsize=10); a2.invert_yaxis()
    for i, c in enumerate(den): a2.text(c["per1000"] + 4, i, f"{c['per1000']:.0f}", va="center", fontsize=9.5, color=MUT)
    a2.set_title("Sea lights per 1,000 km of coast", loc="left", fontsize=11.5); spines(a2); a2.set_xlim(0, den[0]["per1000"] * 1.15)
    for a in (a1, a2): a.set_facecolor(BG); a.tick_params(axis="x", labelsize=9)
    fig.text(.01, .01, f"Coast: Natural Earth 1:10m outlines minus shared borders. Per 1,000 km: {CO['dense_rule']}. World: {CO['world_per1000']:.1f}.", fontsize=9, color=MUT)
    fig.tight_layout(rect=(0, .03, 1, 1)); both(fig, "countries")

    # 5. densest coasts
    rg = R["regions"]["top"][:12] + R["regions"]["top_outside_nordic"][:6]
    fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG); ax.set_facecolor(BG)
    cols = [COOL if r["iso"] in ("SWE", "FIN") else HOT for r in rg]
    ax.barh(range(len(rg)), [r["per100"] for r in rg], color=cols)
    ax.set_yticks(range(len(rg))); ax.set_yticklabels([f"{r['name']}, {r['country']}" for r in rg], fontsize=10); ax.invert_yaxis()
    for i, r in enumerate(rg): ax.text(r["per100"] + .8, i, f"{r['per100']:.1f}  ({r['sea']} lights, {r['coast_km']:,} km)", va="center", fontsize=9, color=MUT)
    ax.axhline(11.5, color=MUT, lw=.6, ls=":"); ax.text(70, 11.75, "outside Sweden and Finland", fontsize=9.5, color=HOT, ha="right", va="top")
    spines(ax); ax.set_xlim(0, 100); ax.set_title(f"Sea lights per 100 km of coast, {R['regions']['rule']}", loc="left", fontsize=11.5)
    fig.tight_layout(); both(fig, "regions")

    # 6. tallest
    tl = R["tallest"]["rows"]
    fig, ax = plt.subplots(figsize=(11, 8.2), facecolor=BG); ax.set_facecolor(BG)
    cols = [INK if re.search(r"stone|granite|brick", t["build"], re.I) else LAMP for t in tl]
    ax.barh(range(len(tl)), [t["m"] for t in tl], color=cols)
    ax.set_yticks(range(len(tl))); ax.set_yticklabels([f"{t['name']}, {t['country']}" for t in tl], fontsize=9); ax.invert_yaxis()
    for i, t in enumerate(tl): ax.text(t["m"] + .6, i, f"{t['m']} m · {t['year']}", va="center", fontsize=8.5, color=MUT)
    ax.set_xlim(0, 100); spines(ax)
    ax.legend(handles=[Rectangle((0, 0), 1, 1, color=INK, label="stone, granite or brick"), Rectangle((0, 0), 1, 1, color=LAMP, label="concrete, iron or steel")], frameon=False, loc="lower right", fontsize=10)
    ax.set_title("The tallest traditional lighthouses, tower height (Wikipedia, List of tallest lighthouses)", loc="left", fontsize=11.5)
    fig.tight_layout(); both(fig, "tallest")

    # 7. coverage
    cv = R["coverage"]["most_bare"] + R["coverage"]["least_bare"]
    fig, ax = plt.subplots(figsize=(11, 5.6), facecolor=BG); ax.set_facecolor(BG)
    ax.barh(range(len(cv)), [c["sl_le1_pct"] for c in cv], color=[HOT if c["sl_le1_pct"] > 50 else COOL for c in cv])
    ax.set_yticks(range(len(cv))); ax.set_yticklabels([f"{c['name']} ({c['n']:,})" for c in cv], fontsize=10); ax.invert_yaxis()
    for i, c in enumerate(cv): ax.text(c["sl_le1_pct"] + 1, i, f"{c['sl_le1_pct']:.0f}%", va="center", fontsize=9.5, color=MUT)
    ax.set_xlim(0, 110); spines(ax)
    ax.set_title("Share of each country's lighthouses with at most one Wikipedia article\n(countries with at least 40; high shares suggest a bulk import from a national list)", loc="left", fontsize=11)
    fig.tight_layout(); both(fig, "coverage")

    # 8. day map coloured by era (paper only, and blog)
    fig = plt.figure(figsize=(13, 7.6), facecolor=BG)
    ax = fig.add_axes([.01, .08, .98, .86]); outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, lw=.25)
    dd = D.assign(x=X, y=Y).sort_values("era", ascending=False)
    ax.scatter(dd.x, dd.y, s=3.2, c=[ECOL[e] for e in dd.era], lw=0, alpha=.85, zorder=3)
    H = [Line2D([], [], ls="", marker="o", ms=7, mfc=e[1], mec="none", label=e[0]) for e in ERAS]
    fig.legend(handles=H, loc="lower center", ncol=7, frameon=False, fontsize=10, bbox_to_anchor=(.5, .005), handletextpad=.3)
    fig.text(.02, .965, "Lighthouses by when they were built or first lit (Wikidata inception)", fontproperties=DISPB, fontsize=17, color=FG, va="center")
    both(fig, "era_map")

    # header card 1200 x 630
    fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
    fig.text(.045, .83, "Lighthouses", fontproperties=DISP, fontsize=60, color=FG, va="center")
    fig.text(.045, .69, "of the world", fontproperties=DISP, fontsize=60, color=LAMP, va="center")
    fig.text(.047, .485, f"Every lighthouse in Wikidata, {R['n']['items']:,} of them,\non one glowing map. The oldest still standing,\nthe tallest, and the 1870s building boom.", fontproperties=SERP, fontsize=17, color=FG, va="center", linespacing=1.4)
    fig.text(.047, .27, f"AD {R['spot']['Tower of Hercules']['year']}", fontproperties=DISP, fontsize=30, color=HOT, va="center")
    fig.text(.047, .215, "Tower of Hercules,\noldest still standing", fontsize=11, color=MUT, va="top")
    fig.text(.27, .27, f"{CO['dense'][0]['per1000']:.0f}", fontproperties=DISP, fontsize=30, color=COOL, va="center")
    fig.text(.27, .215, "lights per 1,000 km\nof coast, Sweden", fontsize=11, color=MUT, va="top")
    fig.text(.047, .07, "maps.tristanhotham.com/lighthouses  ·  Dr Tristan Hotham", fontsize=11, color=MUT, va="center")
    bx = fig.add_axes([.53, .05, .45, .9]); bx.set_facecolor(NSEA)
    night_neu(bx, ext=(-1.15e6, 1.15e6, -1.3e6, 1.3e6), gain=.45, px=(700, 790))
    bx.add_patch(Rectangle((0, 0), 1, 1, transform=bx.transAxes, fc="none", ec=FG, lw=2, zorder=20))
    bx.text(.04, .03, "Northern Europe at night, one glow per lighthouse", transform=bx.transAxes, fontsize=9.5, color="#C9D3E0", zorder=21)
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
    print("figures", sorted(os.listdir(BL)))
