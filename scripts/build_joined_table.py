#!/usr/bin/env python3
"""
Listing (join): construction of the joined neighbourhood table.

Extracted verbatim from the source-code listing (lst:join) of the
manuscript "Soil amplification and collapse screening in Istanbul".
This is the code as documented in the paper; the structural/site
listings (siteresp, mdof, modal) are the representative reference
implementations described there. Verify paths and parameters against
your local environment before running.

Description (from the listing caption):
Construction of the joined neighbourhood table from the two İBB source files. The join key is the numerical UAVT neighbourhood identifier; the four derived columns are the three sums and the ratio defined in the manuscript. The assertions reproduce the consistency checks reported in Section (see manuscript).
"""

import pandas as pd

BLD = "data_Neighborhood-Based Building Numbers for 2017.csv"
SCN = "data_Earthquake Scenario Analysis Results.csv"

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

# Derived columns, Eqs. (nbldg)-(rheavy): three sums and one ratio.
j["n_bldg"]      = j[AGE].sum(axis=1)
j["heavy"]       = j[DMG[0]] + j[DMG[1]]
j["dmg_any"]     = j[DMG].sum(axis=1)
j["heavy_ratio"] = j["heavy"] / j["n_bldg"]

# The storey-class breakdown must reproduce the same building total.
STO = ["1-4 kat_arasi", "5-9 kat_arasi", "9-19 kat_arasi"]
assert (j[STO].sum(axis=1) == j["n_bldg"]).all()
assert j["heavy_ratio"].max() <= 1.0

j.to_csv("mahalle_inventory_scenario_joined.csv", index=False, encoding="utf-8")
