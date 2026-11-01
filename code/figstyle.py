"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the palette, Natural Earth outlines in Equal Earth, and a glow renderer for night maps."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.ndimage import gaussian_filter
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#626A74", "axes.labelcolor": "#1B2230",
                     "xtick.color": "#626A74", "ytick.color": "#626A74"})
BG, FG, MUT, LAND, RULE, SEA = "#F6F4EF", "#1B2230", "#626A74", "#E2DED3", "#DDD8CC", "#E6EDF1"
HOT, LAMP, INK, COOL = "#B3202A", "#D98E04", "#14213D", "#2F6FB0"
NSEA, NLAND, NEDGE = "#081220", "#142031", "#2A3B52"
ECOL = [e[1] for e in ERAS]

EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = [(f["properties"]["iso"], r) for f in W["features"] for r in rings(f["geometry"])]
WORLD_EXT = (-17.0e6, 17.0e6, -8.75e6, 8.7e6)


def proj(lon, lat, tr=EE):
    return tr.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))


def world(ax, tr=EE, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1, clip=None):
    for iso, ring in SHAPES:
        if iso == "ATA" and ext == WORLD_EXT:
            pass
        if clip and (ring[:, 0].max() < clip[0] or ring[:, 0].min() > clip[2] or ring[:, 1].max() < clip[1] or ring[:, 1].min() > clip[3]):
            continue
        x, y = tr.transform(np.clip(ring[:, 0], -179.9, 179.9), np.clip(ring[:, 1], -89.5, 89.5))
        ax.add_patch(MPoly(np.column_stack([x, y]), closed=True, fc=land, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def outline(ax, fc=None, lw=.8, ec=MUT, z=0):
    lat = np.linspace(-90, 90, 181)
    xl, yl = EE.transform(np.full_like(lat, -180), lat); xr, yr = EE.transform(np.full_like(lat, 180), lat[::-1])
    ax.add_patch(MPoly(np.column_stack([np.r_[xl, xr], np.r_[yl, yr]]), closed=True, fc=fc or "none", ec=ec, lw=lw, zorder=z))


def spines(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def lights():
    return pd.read_csv(f"{DATA}/lighthouses.csv", dtype={"name": str, "height_raw": str, "focal_raw": str, "year_all": str, "country_wd": str})


def glow(ax, x, y, ext, px=(1600, 900), sig=(1.2, 5.0), gain=1.0, z=5, col=(1.0, .70, .18)):
    """Additive night glow: count points per pixel, blur at two scales, tone map to amber and then white."""
    w, h = px
    H, _, _ = np.histogram2d(y, x, bins=[h, w], range=[[ext[2], ext[3]], [ext[0], ext[1]]])
    a = gaussian_filter(H, sig[0]) * 1.6 + gaussian_filter(H, sig[1]) * 9.0
    a = 1 - np.exp(-gain * a)
    core = np.clip(gaussian_filter(H, .6) * 1.6, 0, 1)
    img = np.zeros((h, w, 4))
    img[..., 0] = col[0]; img[..., 1] = np.clip(col[1] + .3 * core + .15 * a, 0, 1); img[..., 2] = np.clip(col[2] + .75 * core ** 1.5 + .2 * a ** 2, 0, 1)
    img[..., 3] = np.clip(a * .95 + core * .5, 0, 1)
    ax.imshow(img, extent=(ext[0], ext[1], ext[2], ext[3]), origin="lower", zorder=z, interpolation="bilinear")
