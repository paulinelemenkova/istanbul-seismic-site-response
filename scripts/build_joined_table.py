#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
BLD = DATA / "data_ibb_building_numbers_2017.csv"
SCN = DATA / "data_ibb_scenario_analysis_results.csv"
OUT = DATA / "mahalle_inventory_scenario_joined.csv"

bld = pd.read_csv(BLD, encoding="utf-8-sig")
scn = pd.read_csv(SCN, encoding="utf-8-sig")

AGE = ["1980_oncesi", "1980-2000_arasi", "2000_sonrasi"]
DMG = ["cok_agir_hasarli_bina_sayisi", "agir_hasarli_bina_sayisi",
       "orta_hasarli_bina_sayisi", "hafif_hasarli_bina_sayisi"]

j = bld.merge(scn, left_on="mahalle_uavt", right_on="mahalle_koy_uavt",
              how="inner", suffixes=("", "_s"))

assert len(j) == len(bld) == len(scn) == 959
assert (j.mahalle_uavt == j.mahalle_koy_uavt).all()
assert (j.ilce_adi == j.ilce_adi_s).all()

j["n_bldg"]      = j[AGE].sum(axis=1)
j["heavy"]       = j[DMG[0]] + j[DMG[1]]
j["dmg_any"]     = j[DMG].sum(axis=1)
j["heavy_ratio"] = j["heavy"] / j["n_bldg"]

STO = ["1-4 kat_arasi", "5-9 kat_arasi", "9-19 kat_arasi"]
assert (j[STO].sum(axis=1) == j["n_bldg"]).all()
assert j["heavy_ratio"].max() <= 1.0

OUT.parent.mkdir(parents=True, exist_ok=True)
j.to_csv(OUT, index=False, encoding="utf-8")
print(f"wrote {OUT}  ({len(j)} neighbourhoods, {j['n_bldg'].sum():,} buildings)")
