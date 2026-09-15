#!/usr/bin/env python3

import os, math, re, warnings
import numpy as np
import geopandas as gpd
import xarray as xr
import rasterio.features
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt
from shapely.geometry import shape, Point
import pygmt
warnings.filterwarnings("ignore")
os.environ.setdefault("GMT_LIBRARY_PATH", "/usr/lib/x86_64-linux-gnu")

SHP = "data/DSMW/DSMW.shp"
RELIEF = "data/relief_marmara.nc"
W, E, S, N = 25.8, 31.0, 39.5, 41.9
REGION = [W, E, S, N]
WCOL = "158/202/225"

UNIT = {"Lc": "Chromic Luvisols", "Lo": "Orthic Luvisols", "Be": "Eutric Cambisols",
    "Bk": "Calcic Cambisols", "Vp": "Pellic Vertisols", "Vc": "Chromic Vertisols",
    "Jc": "Calcaric Fluvisols", "Xk": "Calcic Xerosols", "To": "Ochric Andosols",
    "Rc": "Calcaric Regosols", "I": "Lithosols", "E": "Rendzinas"}

PAL = ["251/180/174", "204/235/197", "222/203/228", "254/217/166", "255/255/204",
       "229/216/189", "253/218/236", "179/226/205", "253/205/172", "244/202/228",
       "230/245/201", "255/242/174", "141/211/199", "190/186/218", "253/180/98",
       "179/222/105", "252/205/229"]

g = gpd.read_file(SHP, bbox=(W, S, E, N)).set_crs(4326, allow_override=True)
g = gpd.clip(g, (W, S, E, N))
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g["dom"] = g["DOMSOI"].str.strip()
soils = g[~g["dom"].isin(["WR", "WAT"])].copy()

def smu_code(f):
    f = str(f)
    m = re.match(r"^([A-Za-z]{1,2}\d+)", f)
    return m.group(1) if m else f.split("-")[0]
soils["smu"] = soils["FAOSOIL"].map(smu_code)
smu2dom = soils.groupby("smu")["dom"].agg(lambda s: s.mode().iloc[0]).to_dict()

def dom_of(u):
    if u in smu2dom:
        return smu2dom[u]
    m = re.match(r"^[A-Za-z]{1,2}", u)
    return m.group(0) if m else u
def uname(u):
    return UNIT.get(dom_of(u), dom_of(u))

order = soils.dissolve("smu").geometry.to_crs(3857).area.sort_values(ascending=False).index.tolist()
cid = {u: i + 1 for i, u in enumerate(order)}
col = {u: PAL[i % len(PAL)] for i, u in enumerate(order)}
inv = {v: k for k, v in cid.items()}

rel = xr.load_dataarray(RELIEF, engine="netcdf4")
lon, lat = rel.lon.values, rel.lat.values
nlat, nlon = rel.shape
dx = (lon[-1] - lon[0]) / (nlon - 1); dy = (lat[-1] - lat[0]) / (nlat - 1)
transform = from_origin(lon[0] - dx / 2, lat[-1] + dy / 2, dx, abs(dy))
shapes = [(geom, cid[u]) for geom, u in zip(soils.geometry, soils["smu"])]
ras = np.flipud(rasterio.features.rasterize(shapes, out_shape=(nlat, nlon),
               transform=transform, fill=0, dtype="int32"))
empty = ras == 0
idxf = distance_transform_edt(empty, return_distances=False, return_indices=True)
filled = ras[tuple(idxf)]
land = pygmt.grdlandmask(region=REGION, spacing="15s", registration="pixel",
                         resolution="f", mask_values=[0, 1, 0, 1, 0]).values
soil = np.where(land == 1, filled, np.nan).astype(float)
xr.DataArray(soil, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"),
             name="smu").to_netcdf("soil_units.nc")

land_int_nu = np.flipud(np.where(land == 1, filled, 0).astype("int32"))
recs = list(rasterio.features.shapes(land_int_nu, mask=land_int_nu > 0, transform=transform))
bnd = gpd.GeoDataFrame({"cid": [int(v) for _, v in recs]},
                       geometry=[shape(gj) for gj, _ in recs], crs=4326)
bnd["smu"] = bnd["cid"].map(inv)
bnd["area"] = bnd.geometry.to_crs(3857).area
lab = bnd[bnd["area"] > 1.2e8].copy()
def _n_labels(a):
    return 3 if a > 1.5e9 else (2 if a > 5e8 else 1)
def _spread(geom, n):
    if n <= 1:
        return [geom.representative_point()]
    poly = max(geom.geoms, key=lambda p: p.area) if geom.geom_type == "MultiPolygon" else geom
    x0, y0, x1, y1 = poly.bounds
    cands = [Point(x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))
             for fx in (0.2, 0.35, 0.5, 0.65, 0.8) for fy in (0.3, 0.5, 0.7)]
    cands = [p for p in cands if poly.contains(p)]
    if len(cands) <= 1:
        return [geom.representative_point()]
    chosen = [cands[0]]
    while len(chosen) < n:
        rem = [p for p in cands if p not in chosen]
        if not rem:
            break
        chosen.append(max(rem, key=lambda q: min(q.distance(c) for c in chosen)))
    return chosen[:n]

with open("soil_cat.cpt", "w") as f:
    for u in order:
        i = cid[u]; f.write(f"{i-0.5}\t{col[u]}\t{i+0.5}\t{col[u]}\n")
    f.write("N 255/255/255\n")

water = land != 1
dwater = distance_transform_edt(water)
LO, LA = np.meshgrid(lon, lat)
sw = water & (LO > 25.95) & (LO < 26.6) & (LA > 39.6) & (LA < 40.0)
iy, ix = np.unravel_index(int(np.argmax(np.where(sw, dwater, -1))), dwater.shape)
AEG = (float(lon[ix]), float(lat[iy]))

MW = 19.0
PROJ = f"M{MW}c"
AXES = ["xa1f0.5g1", "ya0.5f0.25g0.5"]
zmax = float(math.ceil(rel.max() / 100) * 100)
pygmt.config(MAP_FRAME_TYPE="fancy", MAP_FRAME_PEN="1.1p,black",
             FONT_ANNOT_PRIMARY="9p,Helvetica", FONT_LABEL="10p,Helvetica",
             MAP_GRID_PEN_PRIMARY="0.5p,white,3_3",
             MAP_TICK_LENGTH_PRIMARY="4p", FORMAT_GEO_MAP="ddd:mmF")
fig = pygmt.Figure()

pygmt.makecpt(cmap="gray", series=[0, zmax], output="relief_grey.cpt")
grad = pygmt.grdgradient(grid=RELIEF, radiance=[315, 30], normalize="t1")
fig.grdimage(grid=RELIEF, cmap="relief_grey.cpt", shading=grad,
             region=REGION, projection=PROJ, transparency=30)
fig.grdimage(grid="soil_units.nc", cmap="soil_cat.cpt",
             transparency=40, nan_transparent=True)
fig.plot(data=bnd, pen="0.25p,139/69/19")

_placed = []
for _, r in lab.sort_values("area", ascending=False).iterrows():
    for p in _spread(r.geometry, _n_labels(r["area"])):
        if any(abs(p.x - qx) < 0.19 and abs(p.y - qy) < 0.085 for qx, qy in _placed):
            continue
        fig.text(x=p.x, y=p.y, text=r["smu"],
                 font="6.5p,Helvetica-Oblique,30/20/10", justify="CM")
        _placed.append((p.x, p.y))

fig.coast(water=WCOL, resolution="f", area_thresh="2",
          shorelines="0.4p,gray15", borders=["1/0.7p,gray25,-"])

fig.text(x=28.18, y=40.70, text="Sea of Marmara",
         font="10p,Helvetica-BoldOblique,20/60/110", justify="CM")
fig.text(x=29.55, y=41.78, text="Black Sea",
         font="10p,Helvetica-BoldOblique,20/60/110", justify="CM")
fig.text(x=AEG[0] + 0.06, y=AEG[1], text="Aegean", justify="BC", offset="0c/0.03c",
         font="8.5p,Helvetica-BoldOblique,20/60/110")
fig.text(x=AEG[0] + 0.06, y=AEG[1], text="Sea", justify="TC", offset="0c/-0.03c",
         font="8.5p,Helvetica-BoldOblique,20/60/110")

fig.plot(x=[28.98], y=[41.01], style="a0.5c", fill="red", pen="1.0p,black")
fig.text(x=28.98, y=41.01, text="Istanbul", font="12p,Helvetica-Bold,black",
         justify="LB", offset="0.26c/0.12c")
CITIES = [(29.06, 40.19, "Bursa", "LM", "0.15c/0c"),
    (26.41, 40.15, "\u00c7anakkale", "TC", "0c/-0.16c"), (26.56, 41.68, "Edirne", "LM", "0.15c/0c"),
    (27.51, 40.98, "Tekirdag", "TC", "0c/-0.16c"), (27.22, 41.73, "Kirklareli", "LM", "0.15c/0c"),
    (29.92, 40.77, "Izmit", "LM", "0.15c/0c"), (30.40, 40.78, "Adapazari", "LM", "0.15c/0c"),
    (29.28, 40.655, "Yalova", "TC", "0c/-0.16c"), (27.97, 40.35, "Bandirma", "TC", "0c/-0.16c"),
    (29.43, 40.80, "Gebze", "RM", "-0.15c/0c"), (28.25, 41.07, "Silivri", "TC", "0c/-0.16c"),
    (27.80, 41.16, "\u00c7orlu", "LM", "0.15c/0c"), (27.36, 41.40, "L\u00fcleburgaz", "RM", "-0.15c/0c")]
for x, y, t, j, off in CITIES:
    fig.plot(x=[x], y=[y], style="c0.11c", fill="black", pen="0.5p,white")
    fig.text(x=x, y=y, text=t, font="7.5p,Helvetica-Bold,black", justify=j, offset=off)

fig.basemap(frame=AXES + ["WSNe"])
with pygmt.config(FONT_ANNOT_PRIMARY="8p"):
    fig.basemap(map_scale="g28.12/40.44+w100k+c40.5+f+u")

spec = ["H 13p,Helvetica-Bold Dominant soil units of the Marmara region  (FAO-74, 3rd level)",
        "D 0.08c 0.6p", "N 4"]
for u in order:
    spec.append(f"S 0.2c s 0.34c {col[u]} 0.2p,gray35 0.66c @%2%{u}@%% {uname(u)}")
spec.append(f"S 0.2c s 0.34c {WCOL} 0.2p,gray35 0.66c Water bodies / lakes")
with open("legend.txt", "w") as f:
    f.write("\n".join(spec) + "\n")
fig.legend(spec="legend.txt", position="JTC+jBC+o0c/0.95c+w20.5c",
           box="+gwhite+p0.9p,gray30+r5p+s3p/-3p/gray60")

fig.colorbar(cmap="relief_grey.cpt",
             position="JBL+jTL+o0c/1.25c+w7c/0.32c+h+ml",
             frame=["xa500f250+lElevation (m) - grey SRTM hillshade"])
fig.text(position="BR", offset="0c/-1.7c",
         text="FAO/UNESCO DSMW soil mapping units \u00b7 SRTM15+ relief \u00b7 PyGMT / GMT 6",
         font="7p,Helvetica,gray40", no_clip=True)

fig.savefig("fig06_soils.pdf")
fig.savefig("fig06_soils.png", dpi=300)
print("classes=%d  labels=%d  units:" % (len(order), len(lab)), order)
