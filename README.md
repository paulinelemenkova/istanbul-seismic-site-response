# Soil amplification and collapse screening in Istanbul

Code and data for the manuscript *Soil amplification and collapse screening in
Istanbul: a machine-learning model of structural vulnerability*.

The repository contains the reproducible workflow behind the paper: the
construction of the regional geospatial dataset, the site- and structural-response
modelling, the resist/collapse labelling and machine-learning validation, and the
figure-generation scripts. Submitted to *Geohazards & Remediation* (Higher
Education Press, ISSN 2097-5627).

> Lemenkova, P. and Zülfikar, A. C. *Soil amplification and collapse screening in
> Istanbul: a machine-learning model of structural vulnerability.* Geohazards &
> Remediation (submitted). Volume, year and DOI will be added on acceptance.

Archived release: https://zenodo.org/records/21840346

## Layout

```
scripts/    methodology and figure-generation scripts (Python 3.12 / GMT 6.x)
data/       input tables and grids
palettes/   colour palettes (cpt-city), retained for exact reproduction
```

## Scripts

**Methodology** (the mechanics described in the paper):

| Script | Purpose |
|---|---|
| `build_joined_table.py` | Inner-join the two raw İBB tables on the numerical UAVT key and derive the count/ratio columns → `mahalle_inventory_scenario_joined.csv` |
| `sample_vs30.py` | Sample the USGS hybrid Vs30 mosaic at each neighbourhood centroid and polygon mean |
| `site_amplification.py` | One-dimensional linear (elastic) site-amplification transfer function and site period |
| `mdof_shear_building.py` | MDOF shear-building model; generalised eigenproblem → height, modal periods, effective-mass fractions |
| `modal_response_spectrum.py` | EC8/TBEC design spectrum and response-spectrum modal analysis (SRSS) |
| `shap_attribution.py` | SHAP (TreeExplainer) feature attribution of the fitted resist/collapse classifier |
| `run_validation.py` | Leakage-controlled ablation and spatial (5 km block / leave-one-district-out) validation |

`site_amplification.py`, `mdof_shear_building.py` and `modal_response_spectrum.py`
are the representative reference implementations described in the paper; run them
against your own inputs to reproduce the reported factors, periods and base shears.
`shap_attribution.py` consumes the fitted classifier and the standardised test
features. `run_validation.py` expects a CSV of the 2 800 labelled analysis cells
(`site_structure_features.csv`); the spatially independent designs it implements
are reported in the paper as specified but not-yet-executed.

**Figures.** The `figNN_*.{py,sh}` scripts generate the manuscript figures
(GMT 6.x modern mode for the `.sh` maps, Matplotlib for the `.py` panels).

## Requirements

Python 3.12 with NumPy, pandas, SciPy, Matplotlib, xarray, shapely, pyshp,
scikit-learn, and (optionally) xgboost and shap; GMT 6.x (modern mode) for the
shell scripts; Nimbus Sans (`fonts-urw-base35`). Without `xgboost`,
`run_validation.py` falls back to scikit-learn's `HistGradientBoostingClassifier`
and reports that it did so.

Two inputs are **not** redistributed here and must be downloaded before the
scripts that need them will run:

| File | Source |
|---|---|
| `ne_10m_land.{shp,shx,dbf}` | Natural Earth 1:10 m physical, public domain — https://github.com/nvkelso/natural-earth-vector |
| `global_vs30.grd` | USGS global hybrid Vs30 mosaic — https://earthquake.usgs.gov/data/vs30 |

Place both in `data/`. The window used throughout is 27.80–30.00 °E,
40.55–41.50 °N.

## Data provenance

| File | Description | Source and terms |
|---|---|---|
| `data_ibb_building_numbers_2017.csv` | Building counts by neighbourhood, construction period and storey class | İBB Open Data, 959 *mahalle* |
| `data_ibb_scenario_analysis_results.csv` | Damage states, casualties, lifeline damage and shelter demand for the night-time Mw 7.5 Main Marmara Fault scenario | İBB Open Data |
| `mahalle_inventory_scenario_joined.csv` | The two tables above joined on the numerical UAVT code (959/959 matched) by `build_joined_table.py` | derived here |
| `mahalle_with_coords.csv`, `mahalle_vs30.csv` | Neighbourhood centroids, areas and sampled Vs30 | derived here |
| `mahalle_fixed.geojson`, `ilce_fixed.geojson` | Neighbourhood and district boundaries | OpenStreetMap via Nominatim, ODbL |
| `vs30_istanbul.tif`, `vs30.nc` | Vs30 cut to the study window | USGS hybrid mosaic (Heath et al. 2020), public domain |
| `amp.nc`, `amp_panel.nc` | Site amplification factor F, derived here (see `site_amplification.py`) | derived here |
| `epicentres.txt`, `marmara_meca.txt` | Earthquake epicentres and moment tensors | KOERI; Global CMT |
| `faults_marmara.gmt`, `extra_faults.txt` | Fault traces | as cited in the manuscript |

Two joins are used and should not be confused. The inventory–scenario join above
is an attribute join on the numerical UAVT identifier and matches all 959
neighbourhoods. Separately, for mapping, neighbourhood values are matched to
boundary polygons; because the neighbourhood names in the İBB CSVs are mojibake
(`İ` appears as `Ý`, `Ş` as `Þ`), that step is spatial (centroid-in-polygon) and
places 912 of 959 neighbourhoods, the remainder drawn as no-data rather than
interpolated.

## Colour palettes

From [cpt-city](http://soliton.vm.bytemark.co.uk/pub/cpt-city/). Terms as
published there:

| File | Collection | Terms |
|---|---|---|
| `indigo-orange.cpt` | ocal (Alan Horkan, 2004) | public domain |
| `aquamarinemermaid.cpt`, `girlcat.cpt`, `autumnrose.cpt` | rc (Restless Concepts) | free to use |
| `qual-mixed-12.cpt` | ssz (Statistik Stadt Zürich / Interactive Things) | **CC BY-SA 4.0 — attribution required** |

## Not included

The feature-importance (SHAP) figure is not shipped as a ready-to-run figure
script: its published panels require the TreeSHAP output of the fitted
classifier, and `shap_attribution.py` provides the code that produces those
attributions from the model. Any other figure whose inputs are not public is
likewise omitted rather than shipped in a state that would produce a figure
differing from the published one. See the manuscript for the figures concerned.
