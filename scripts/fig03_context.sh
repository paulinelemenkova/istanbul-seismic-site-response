#!/usr/bin/env bash
# =====================================================================
# fig15_context.sh
# Regional seismotectonic context of the Istanbul-Marmara region.
# Generic Mapping Tools (GMT) 6, modern mode.
#
# Layers: real GSHHG coastlines + honest land/sea fill; North Anatolian
# Fault system (Main Marmara Fault + secondary strands); regional active-
# fault database (flt4_2l); instrumental seismicity from the IEB catalogue
# coloured by magnitude; labelled large/historical earthquakes;
# representative seismic monitoring network; plate setting and relative-
# motion vector; full cartographic furniture.
#
# Inputs (working dir):
#   main_marmara_fault.txt  secondary_faults.txt  hist_eq.txt  stations.txt
#   IEB_export_1_.csv       seismic catalogue export (Year,Month,Day,Time,
#                           Lat,Lon,Depth,Mag,Region,Timestamp)
#   flt4_2l.shp (+.shx/.dbf/.prj)  regional active-fault shapefile
#
# OPTIONAL real relief: drop a GEBCO/ETOPO grid in the working dir and
# uncomment the grdimage block (#> EDIT A) to replace the flat sea fill
# with shaded bathymetry-topography.
#
# Run:  bash fig15_context.sh         -> fig15_context.pdf + fig15_context.png
# =====================================================================
set -e

REG=-R26/31.3/39.6/41.5            # W/E/S/N  (Sea of Marmara + Istanbul)
PROJ=-JM16c                        # Mercator, 16 cm wide
OUT=fig15_context

# ----------------------------------------------------------- data preparation
# (a) Instrumental seismicity from the IEB catalogue export -> lon lat mag size.
#     Fields 5,6,8 (Lat,Lon,Mag) are read directly; they precede the quoted
#     "Region" field, so a plain comma split is safe. Size grows with magnitude.
awk -F, 'NR>1 {lat=$5+0; lon=$6+0; mag=$8+0;
        if(lon>=26 && lon<=31.3 && lat>=39.6 && lat<=41.5 && mag>0){
            s=0.045+0.075*(mag-1.5); if(s>0.42)s=0.42; if(s<0.05)s=0.05;
            printf "%.4f %.4f %.2f %.3f\n", lon, lat, mag, s}}' \
    IEB_export_1_.csv > seismicity.txt

# (b) Active-fault database: reproject flt4_2l.shp (Europe Lambert Conformal
#     Conic, metres) to WGS84 once; GMT then clips it to the map region.
#     Requires GDAL (ogr2ogr).
if [ ! -f flt4_2l.gmt ] && [ -f flt4_2l.shp ]; then
    ogr2ogr -t_srs EPSG:4326 -f OGR_GMT flt4_2l.gmt flt4_2l.shp
fi

# ----------------------------------------------------------- house style
gmt set FORMAT_GEO_MAP=dddF \
        MAP_FRAME_TYPE=plain MAP_FRAME_PEN=0.9p,gray25 \
        MAP_TICK_PEN_PRIMARY=0.7p,gray25 \
        MAP_GRID_PEN_PRIMARY=0.35p,white \
        FONT_TITLE=15p,Helvetica-Bold,black \
        FONT_ANNOT_PRIMARY=8p,Helvetica,gray15 \
        FONT_LABEL=9p,Helvetica,gray15

gmt begin ${OUT} pdf,png E400

  # ---------------------------------------- 1. basemap fill + coastlines
  # Honest flat land/sea fill from full-resolution GSHHG coastlines.
  gmt coast $REG $PROJ -Df \
      -G244/238/224 -Slightsteelblue@30 \
      -W0.3p,gray40 -N1/0.5p,gray55,- -Ia/0.3p,steelblue

  #> EDIT A (optional real relief) — uncomment with a GEBCO/ETOPO grid present:
  # gmt makecpt -Cgeo -T-1500/1500 -H > topo.cpt
  # gmt grdimage marmara_relief.nc -Ctopo.cpt -I+a315+ne0.6
  # gmt coast -Df -W0.3p,gray40 -N1/0.5p,gray55,-

  # ---------------------------------------- 2. instrumental seismicity (background)
  # colour = magnitude (stepped `seis` CPT); size grows with magnitude.
  gmt makecpt -Cseis -T1.5/5/0.5 -Z -I -H > seis.cpt
  gmt plot seismicity.txt -i0,1,2,3 -Sc -Cseis.cpt -W0.15p,gray30 -t25

  # ---------------------------------------- 3. fault system (drawn over seismicity)
  [ -f flt4_2l.gmt ] && gmt plot flt4_2l.gmt -W0.6p,gray20       # regional active faults (flt4_2l)
  gmt plot secondary_faults.txt -W1.4p,firebrick,4_2:0p        # other NAF strands (dashed)
  gmt plot main_marmara_fault.txt -W2.4p,red2                   # Main Marmara Fault (solid)
  gmt plot main_marmara_fault.txt -W0.6p,white,.               # thin white centreline for contrast

  # ---------------------------------------- 4. large / historical earthquakes
  # gold stars sized by magnitude, drawn on top, with year labels.
  gmt plot hist_eq.txt -i0,1,2+s0.115 -Sa -Ggold -W0.9p,black
  gmt text hist_labels.txt -F+f8p,Helvetica-Bold,black -Gwhite@25 -W0.2p,gray70

  # ---------------------------------------- 5. monitoring network
  gmt plot stations.txt -St0.28c -Gdodgerblue3 -W0.4p,white

  # ---------------------------------------- 6. plate setting + motion vector
  # Anatolia moves ~WSW relative to a fixed Eurasia at ~20-25 mm/yr.
  gmt plot -Sv0.5c+ea+h0.5 -Gorange -W2.4p,orange <<'EOF'
29.65 39.84 192 2.8c
EOF
  gmt text -N -F+f8.5p,Helvetica-BoldOblique,gray20+jRM <<'EOF'
29.80 39.74 ~20-25 mm/yr
EOF
  # plate names — letter-spaced caps, gold, no background, smaller font
  gmt text -N -F+f10p,Helvetica-Bold,gold2+jCM <<'EOF'
27.00 41.37 E U R A S I A N   P L A T E
EOF
  gmt text -N -F+f10p,Helvetica-Bold,gold2+jCM <<'EOF'
30.35 39.76 A N A T O L I A N   B L O C K
EOF

  # ---------------------------------------- 7. water-body labels (white italic)
  gmt text -N -F+f12p,Helvetica-Oblique,white+jCM <<'EOF'
28.30 40.62 Sea of Marmara
30.55 41.40 Black Sea
EOF
  # Aegean Sea — rotated 90 deg CCW, stretched along the left border
  gmt text -N -F+f12p,Helvetica-Oblique,white+a90+jCM <<'EOF'
26.13 40.12 Aegean Sea
EOF
  gmt text -N -F+f7.5p,Helvetica-Oblique,white+jCM <<'EOF'
26.55 40.55 Gulf of Saros
29.70 40.755 Gulf of Izmit
EOF

  # ---------------------------------------- 8. city labels (dark, white halo)
  gmt text -N -F+f8.5p,Helvetica-Bold,black+jBL -D0.14c/0.14c -Gwhite@30 <<'EOF'
29.00 41.03 Istanbul
29.97 40.79 Izmit
27.51 40.99 Tekirdag
27.97 40.37 Bandirma
29.06 40.20 Bursa
29.28 40.67 Yalova
EOF

  # ---------------------------------------- 9. frame, graticule, title
  gmt basemap -Bxa1f0.5g1 -Bya0.5f0.25g1 -BWeSn+t"Seismotectonic context of the Istanbul-Marmara region"

  # ---------------------------------------- 10. scale bar + north arrow
  gmt basemap -LjBL+w50k+o0.7c/0.7c+f+l"km"+u --FONT_LABEL=8p,Helvetica,black
  gmt basemap -TdjBL+w0.9c+o1.0c/1.65c+f2+l,,,N --FONT_TITLE=9p

  # ---------------------------------------- 11. magnitude colour bar (OUTSIDE, left, vertical)
  # 10 minor ticks between annotations (f0.1); no panel/border frame.
  gmt colorbar -Cseis.cpt -DJML+w6.6c/0.32c+o1.6c/0c+ml+e \
      -Bxa1f0.1+l"Instrumental seismicity: magnitude M" \
      --FONT_ANNOT_PRIMARY=7.5p --FONT_LABEL=8p

  # ---------------------------------------- 12. symbol legend (OUTSIDE, below map, 2 rows)
  gmt legend -DJBC+w16c+o0c/1.25c+jTC -F+gwhite@12+p0.5p,gray55+r2p --FONT=8p,Helvetica <<'EOF'
N 3
S 0.30c a 0.34c gold 0.9p,black 0.75c Historical EQ (Mw 6+)
S 0.30c t 0.26c dodgerblue3 0.4p,white 0.75c Seismic station (repr.)
S 0.30c v 0.55c orange 2.0p,orange 0.75c Plate motion (Anatolia)
S 0.30c - 0.55c - 2.4p,red2 0.75c Main Marmara Fault
S 0.30c - 0.55c - 1.4p,firebrick,4_2:0p 0.75c Other NAF strand
S 0.30c - 0.55c - 0.6p,gray20 0.75c Active faults (flt4_2l)
EOF

gmt end

echo "wrote ${OUT}.pdf and ${OUT}.png"
