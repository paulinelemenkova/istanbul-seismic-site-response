#!/usr/bin/env python3
"""
build_joined_table.py -- construction of the joined neighbourhood table.

Reproduces the code documented in the manuscript
"Soil amplification and collapse screening in Istanbul: a machine-learning
model of structural vulnerability".

It performs an inner join of the two raw Istanbul Metropolitan Municipality
(IBB) tables on the numerical UAVT neighbourhood identifier (never on the
name: the 959 records carry only 766 distinct names), derives the four
count/ratio columns, runs the consistency assertions reported in the paper,
and writes mahalle_inventory_scenario_joined.csv.

Paths are resolved relative to this file, so the script can be run from any
working directory as long as the repository layout (scripts/ and data/) is
preserved:

    python3 scripts/build_joined_table.py
"""

from pathlib import Path
import pandas as pd

# Repository data directory, resolved relative to this script (scripts/ -> ../data)
DATA = Path(__file__).resolve().parent.parent / "data"
BLD = DATA / "data_ibb_building_numbers_2017.csv"        # building counts, 2017
SCN = DATA / "data_ibb_scenario_analysis_results.csv"    # Mw 7.5 MMF scenario
OUT = DATA / "mahalle_inventory_scenario_joined.csv"

# Both files are UTF-8 with a byte-order mark.
bld = pd.read_csv(BLD, encoding="utf-8-sig")
scn = pd.read_csv(SCN, encoding="utf-8-sig")

AGE = ["1980_oncesi", "1980-2000_arasi", "2000_sonrasi"]
DMG = ["cok_agir_hasarli_bina_sayisi", "agir_hasarli_bina_sayisi",
       "orta_hasarli_bina_sayisi", "hafif_hasarli_bina_sayisi"]

# Inner join on the numerical UAVT identifier, never on the name:
# 959 records carry only 766 distinct neighbourhood names.
j = bld.merge(scn, left_on="mahalle_uavt", right_on="mahalle_koy_uavt",
              how="inner", suffixes=("", "_s"))

assert len(j) == len(bld) == len(scn) == 959      # nothing lost or duplicated
assert (j.mahalle_uavt == j.mahalle_koy_uavt).all()
assert (j.ilce_adi == j.ilce_adi_s).all()         # districts agree everywhere

# Derived columns (three sums and one ratio).
j["n_bldg"]      = j[AGE].sum(axis=1)
j["heavy"]       = j[DMG[0]] + j[DMG[1]]
j["dmg_any"]     = j[DMG].sum(axis=1)
j["heavy_ratio"] = j["heavy"] / j["n_bldg"]

# The storey-class breakdown must reproduce the same building total.
STO = ["1-4 kat_arasi", "5-9 kat_arasi", "9-19 kat_arasi"]
assert (j[STO].sum(axis=1) == j["n_bldg"]).all()
assert j["heavy_ratio"].max() <= 1.0

OUT.parent.mkdir(parents=True, exist_ok=True)
j.to_csv(OUT, index=False, encoding="utf-8")
print(f"wrote {OUT}  ({len(j)} neighbourhoods, {j['n_bldg'].sum():,} buildings)")
