#!/usr/bin/env python3
"""
sample_vs30.py -- clip the USGS global Vs30 grid to the Istanbul window and
sample it at the 959 mahalle of the IBB building inventory.

Produces mahalle_vs30.csv, which adds to mahalle_with_coords.csv:

    vs30_point      Vs30 at the mahalle centroid            (m/s)
    vs30_mean       area-mean Vs30 over the mahalle polygon (m/s, if geometry given)
    vs30_min/max    range within the polygon                (m/s)
    vs30_flag       "ok", "water" (grid returns exactly 600 over water),
                    "nodata", or "no_geometry"

Inputs, all expected in ~/Downloads by default
----------------------------------------------
    global_vs30.grd            USGS global Vs30 mosaic, 631 MB
                               https://earthquake.usgs.gov/data/vs30
    mahalle_with_coords.csv    inventory + centroid lon/lat
    mahalle_fixed.geojson      mahalle polygons (optional, enables area means)

Requirements
------------
    pip install rasterio pandas numpy
    pip install rasterstats            # optional, for the area means
    GMT 6 on PATH                      # optional; used for the clip if present

Usage
-----
    python3 sample_vs30.py                      # everything from ~/Downloads
    python3 sample_vs30.py --dir /some/folder
    python3 sample_vs30.py --no-zonal           # centroid sampling only
"""
import argparse
import os
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

# Istanbul-Marmara analysis window (lon_min, lon_max, lat_min, lat_max)
REGION = (27.4, 30.1, 40.5, 41.6)
WATER_VALUE = 600.0          # the USGS grid assigns exactly 600 m/s over water


def clip_grid(src, dst_tif):
    """Cut the global grid to REGION and write a GeoTIFF.

    Uses GMT when available (fastest and handles the native .grd cleanly),
    otherwise falls back to GDAL through rasterio.
    """
    w, e, s, n = REGION
    if shutil.which("gmt"):
        tmp = dst_tif.replace(".tif", ".grd")
        print("  clipping with GMT ...")
        subprocess.run(["gmt", "grdcut", src,
                        "-R%s/%s/%s/%s" % (w, e, s, n), "-G" + tmp], check=True)
        subprocess.run(["gmt", "grdconvert", tmp,
                        "-G%s=gd:GTiff" % dst_tif], check=True)
        os.remove(tmp)
    else:
        print("  GMT not found; clipping with rasterio ...")
        import rasterio
        from rasterio.windows import from_bounds
        with rasterio.open(src) as ds:
            win = from_bounds(w, s, e, n, ds.transform)
            arr = ds.read(1, window=win)
            prof = ds.profile
            prof.update(driver="GTiff", height=arr.shape[0], width=arr.shape[1],
                        transform=ds.window_transform(win), count=1)
            prof.pop("blockxsize", None); prof.pop("blockysize", None)
            with rasterio.open(dst_tif, "w", **prof) as out:
                out.write(arr, 1)
    return dst_tif


def main():
    ap = argparse.ArgumentParser()
    home_dl = os.path.expanduser("~/Downloads")
    ap.add_argument("--dir", default=home_dl, help="folder holding the inputs")
    ap.add_argument("--grid", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--geojson", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-zonal", action="store_true")
    a = ap.parse_args()

    D = a.dir
    grid = a.grid or os.path.join(D, "global_vs30.grd")
    csv = a.csv or os.path.join(D, "mahalle_with_coords.csv")
    gj = a.geojson or os.path.join(D, "mahalle_fixed.geojson")
    out = a.out or os.path.join(D, "mahalle_vs30.csv")
    clipped = os.path.join(D, "vs30_istanbul.tif")

    for f, what in [(grid, "Vs30 grid"), (csv, "centroid table")]:
        if not os.path.exists(f):
            sys.exit("missing %s: %s" % (what, f))

    try:
        import rasterio
    except ImportError:
        sys.exit("rasterio is required:  pip install rasterio")

    # ---- 1. clip ---------------------------------------------------------- #
    print("[1/4] clipping the global grid to the Istanbul window")
    if os.path.exists(clipped):
        print("  %s already exists; reusing it" % os.path.basename(clipped))
    else:
        clip_grid(grid, clipped)
    with rasterio.open(clipped) as src:
        print("  clipped raster: %d x %d cells, CRS %s"
              % (src.width, src.height, src.crs))

    # ---- 2. centroid sampling --------------------------------------------- #
    print("[2/4] sampling at mahalle centroids")
    d = pd.read_csv(csv)
    if not {"lon", "lat"} <= set(d.columns):
        sys.exit("%s must contain lon and lat columns" % csv)
    ok = d.lon.notna() & d.lat.notna()
    print("  %d of %d rows carry coordinates" % (ok.sum(), len(d)))

    with rasterio.open(clipped) as src:
        nodata = src.nodata
        vals = np.full(len(d), np.nan)
        pts = list(zip(d.loc[ok, "lon"], d.loc[ok, "lat"]))
        vals[ok.values] = [v[0] for v in src.sample(pts)]
    if nodata is not None:
        vals = np.where(vals == nodata, np.nan, vals)
    d["vs30_point"] = np.round(vals, 1)

    # ---- 3. area means over the polygons ---------------------------------- #
    d["vs30_mean"] = np.nan
    d["vs30_min"] = np.nan
    d["vs30_max"] = np.nan
    if not a.no_zonal and os.path.exists(gj):
        try:
            import json
            from rasterstats import zonal_stats
            from shapely.geometry import shape
            print("[3/4] computing area means over the mahalle polygons")
            g = json.load(open(gj, encoding="utf-8"))
            # all_touched=True is essential: many urban mahalle are smaller
            # than a 30 arcsec cell (~0.77 km), so with the default no cell
            # centre falls inside them and the mean returns None.
            st = zonal_stats(g["features"], clipped,
                             stats=["mean", "min", "max"], all_touched=True,
                             nodata=nodata if nodata is not None else -32768)
            # Match polygons to rows by their centroid, which is exactly how the
            # lon/lat columns of mahalle_with_coords.csv were produced. This is
            # exact, unlike matching on mahalle names (959 rows carry only 766
            # distinct names).
            lut = {}
            for f, s_ in zip(g["features"], st):
                c = shape(f["geometry"]).centroid
                lut[(round(c.x, 6), round(c.y, 6))] = s_
            keys = list(zip(d.lon.round(6), d.lat.round(6)))
            pick = lambda k, f_: (lut[k][f_] if k in lut and lut[k][f_] is not None
                                  else float("nan"))
            d["vs30_mean"] = [round(pick(k, "mean"), 1) for k in keys]
            d["vs30_min"] = [pick(k, "min") for k in keys]
            d["vs30_max"] = [pick(k, "max") for k in keys]
            print("  area means obtained for %d mahalle" % d.vs30_mean.notna().sum())
        except ImportError:
            print("[3/4] rasterstats not installed; skipping area means "
                  "(pip install rasterstats)")
    else:
        print("[3/4] no polygon file; skipping area means")

    # Where no polygon mean could be computed, fall back to the point value so
    # that a usable Vs30 exists for every mahalle carrying coordinates.
    d["vs30_used"] = d.vs30_mean.fillna(d.vs30_point)
    d["vs30_source"] = np.where(d.vs30_mean.notna(), "polygon mean",
                       np.where(d.vs30_point.notna(), "centroid point", "none"))

    # ---- 4. flag and write ------------------------------------------------ #
    print("[4/4] flagging and writing")
    flag = np.where(d.vs30_point.isna(), "nodata",
           np.where(np.isclose(d.vs30_point, WATER_VALUE), "water", "ok"))
    flag = np.where(d.lon.isna(), "no_geometry", flag)
    d["vs30_flag"] = flag
    d.to_csv(out, index=False, encoding="utf-8")

    print("\nwrote %s" % out)
    print(d.vs30_flag.value_counts().to_string())
    good = d[d.vs30_flag == "ok"]
    if len(good):
        print("\nVs30 at centroids (flag == ok), n = %d" % len(good))
        print(good.vs30_point.describe().round(1).to_string())
        nw = (d.vs30_flag == "water").sum()
        if nw:
            print("\n%d centroid(s) returned exactly %.0f m/s, the value the USGS "
                  "grid assigns to water." % (nw, WATER_VALUE))
            print("Inspect these before use -- the centroid probably falls "
                  "offshore; use vs30_mean instead:")
            print(d.loc[d.vs30_flag == "water",
                        ["ilce_adi", "mahalle_adi", "lon", "lat"]]
                  .head(10).to_string(index=False))


if __name__ == "__main__":
    main()
