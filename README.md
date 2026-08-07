# Soil amplification and earthquake-induced collapse potential in Istanbul

Code and data for the manuscript *Soil amplification and earthquake-induced
collapse potential in Istanbul: A physics-guided machine-learning framework with
physically interpretable features for Marmara basin effects and structural
vulnerability*.

Scripts and input data for the figures of the accompanying manuscript on soil
amplification and earthquake-induced collapse potential in Istanbul, submitted
to *Geohazards & Remediation* (Higher Education Press, ISSN 2097-5627).

Lemenkova, P. and Zülfikar, A. C. Soil amplification and earthquake-induced
collapse potential in Istanbul: A physics-guided machine-learning framework with
physically interpretable features for Marmara basin effects and structural
vulnerability. *Geohazards & Remediation* (submitted).
Volume, year and DOI will be added on acceptance.

## Layout

```
scripts/    figure-generating scripts (Python 3.12 / GMT 6.x)
data/       input tables and grids
palettes/   colour palettes (cpt-city), retained for exact reproduction
```

## Requirements

Python 3.12 with NumPy, pandas, Matplotlib, SciPy, shapely, pyshp, xarray;
GMT 6.x (modern mode) for the shell scripts; Nimbus Sans (`fonts-urw-base35`).

Two inputs are **not** redistributed here and must be downloaded before the
scripts that need them will run:

| File | Source |
|---|---|
| `ne_10m_land.{shp,shx,dbf}` | Natural Earth 1:10 m physical, public domain — https://github.com/nvkelso/natural-earth-vector |
| `global_vs30.grd` | USGS global hybrid Vs30 mosaic — https://earthquake.usgs.gov/data/vs30 |

Place both in `data/`. The window used throughout is
27.80–30.00 °E, 40.55–41.50 °N.

## Data provenance

| File | Description | Source and terms |
|---|---|---|
| `data_ibb_building_numbers_2017.csv` | Building counts by neighbourhood, construction period and storey class | İBB Open Data, 959 *mahalle* |
| `data_ibb_scenario_analysis_results.csv` | Damage states, casualties, lifeline damage and shelter demand for the night-time Mw 7.5 Main Marmara Fault scenario | İBB Open Data |
| `mahalle_inventory_scenario_joined.csv` | The two tables above joined on the UAVT neighbourhood code (959/959 matched) | derived here |
| `mahalle_with_coords.csv`, `mahalle_vs30.csv` | Neighbourhood centroids, areas and sampled Vs30 | derived here |
| `mahalle_fixed.geojson`, `ilce_fixed.geojson` | Neighbourhood and district boundaries | OpenStreetMap via Nominatim, ODbL |
| `vs30_istanbul.tif`, `vs30.nc` | Vs30 cut to the study window | USGS hybrid mosaic (Heath et al. 2020), public domain |
| `amp.nc`, `amp_panel.nc` | Amplification factor F = (760/Vs30)^m | derived here |
| `epicentres.txt`, `marmara_meca.txt` | Earthquake epicentres and moment tensors | KOERI; Global CMT |
| `faults_marmara.gmt`, `extra_faults.txt` | Fault traces | as cited in the manuscript |

Neighbourhood names in the İBB CSVs are mojibake (`İ` appears as `Ý`, `Ş` as
`Þ`). The join is therefore spatial, matching each centroid to the polygon that
contains it; 912 of 959 resolve, and the remainder are drawn as no-data rather
than interpolated.

## Colour palettes

From [cpt-city](http://soliton.vm.bytemark.co.uk/pub/cpt-city/). Terms as
published there:

| File | Collection | Terms |
|---|---|---|
| `indigo-orange.cpt` | ocal (Alan Horkan, 2004) | public domain |
| `aquamarinemermaid.cpt`, `girlcat.cpt`, `autumnrose.cpt` | rc (Restless Concepts) | free to use |
| `qual-mixed-12.cpt` | ssz (Statistik Stadt Zürich / Interactive Things) | **CC BY-SA 4.0 — attribution required** |

## Not included

Figures whose inputs are not public, or whose scripts still contain placeholder
blocks in place of model output, are omitted rather than shipped in a state that
would produce a figure differing from the published one. See the manuscript for
the figures concerned.
