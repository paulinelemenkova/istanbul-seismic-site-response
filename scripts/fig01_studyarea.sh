#!/usr/bin/env bash
set -e

REG=-R25/31/39/42
PROJ=-JM16c
OUT=fig01_studyarea

GEBCO_TIF=gebco_2026_n42_0_s39_0_w25_0_e31_0_geotiff.tif
[ -f marmara_relief.nc ] || gmt grdconvert "$GEBCO_TIF" marmara_relief.nc

gmt set FORMAT_GEO_MAP=dddF \
        MAP_FRAME_TYPE=plain MAP_FRAME_PEN=0.9p,gray25 \
        MAP_TICK_PEN_PRIMARY=0.7p,gray25 \
        MAP_GRID_PEN_PRIMARY=0.35p,white \
        FONT_TITLE=15p,Helvetica-Bold,black \
        FONT_ANNOT_PRIMARY=8p,Helvetica,gray15 \
        FONT_LABEL=9p,Helvetica,gray15

gmt begin ${OUT} pdf,png E400

  gmt makecpt -Cgeo -T-2200/2500 -H > topo.cpt

  gmt grdimage marmara_relief.nc -Ctopo.cpt -I+a315+ne0.8 $REG $PROJ

  gmt coast -Df -W0.4p,gray20 -N1/0.6p,gray25,- -C150/195/225 \
            -I1/0.4p,steelblue -I2/0.25p,steelblue

  gmt grdcontour marmara_relief.nc -C1000 -W0.3p,gray25@25

  gmt colorbar -Ctopo.cpt -DJML+w9c/0.34c+o1.6c/0c+ml+e \
      -Bxa1000f200+l"Elevation / bathymetry (m)" -By \
      --FONT_LABEL=9p,black --FONT_ANNOT_PRIMARY=8p,black

  gmt plot -Sc0.13c -Gyellow -W0.4p,black <<'EOF'
29.92 40.77
27.51 40.98
29.06 40.19
27.97 40.35
26.41 40.15
29.43 40.80
29.22 40.66
30.40 40.78
26.56 41.68
27.22 41.74
27.36 41.40
27.80 41.16
28.25 41.07
26.67 40.41
27.24 40.23
28.88 40.38
29.72 40.43
26.63 40.85
28.36 40.21
EOF
  gmt plot -Sc0.34c -Gyellow -W0.7p,black <<'EOF'
28.98 41.01
EOF

  gmt text -N -F+f13p,Helvetica-Oblique,white+jCM <<'EOF'
28.833 41.80 Black Sea
EOF
  gmt text -N -F+f11p,Helvetica-Oblique,dodgerblue+jCM <<'EOF'
28.30 40.6667 Sea of Marmara
EOF
  gmt text -N -F+f13p,Helvetica-Oblique,dodgerblue+jCM <<'EOF'
25.55 39.70 Aegean Sea
EOF
  gmt text -N -F+f8p,Helvetica-Oblique,white+jCM <<'EOF'
26.45 40.55 Gulf of Saros
EOF
  gmt text -N -F+f8.5p,Helvetica-Bold,black+jLB -D0.10c/0.10c -Gwhite@30 <<'EOF'
29.92 40.78 Izmit
27.51 40.99 Tekirdag
29.06 40.20 Bursa
27.97 40.36 Bandirma
26.41 40.16 Canakkale
29.43 40.81 Gebze
29.22 40.67 Yalova
30.40 40.79 Adapazari
26.56 41.69 Edirne
27.22 41.75 Kirklareli
27.36 41.41 Luleburgaz
27.80 41.17 Corlu
28.25 41.08 Silivri
26.67 40.42 Gelibolu
27.24 40.24 Biga
28.88 40.39 Mudanya
29.72 40.44 Iznik
26.63 40.86 Kesan
28.36 40.22 Karacabey
EOF
  gmt text -N -F+f14p,Helvetica-Bold,black+jLB -D0.18c/0.16c -Gwhite@25 <<'EOF'
28.98 41.02 Istanbul
EOF

  gmt basemap -Bxa1f0.5g1 -Bya1f0.5g1 -BWeSn+t"Study area: the Sea of Marmara and Istanbul"

  gmt basemap -LjBL+w100k+o0.7c/0.7c+f+l"km"+u --FONT_LABEL=8p,Helvetica,black
  gmt basemap -TdjTL+w0.9c+o0.7c/0.7c+f2+l,,,N --FONT_TITLE=9p

  gmt inset begin -DjTR+w2.4c+o0.22c/0.22c -F+gwhite@10+p0.6p,gray55+r2p
    gmt coast -Rg -JG30/40/2.4c -Da -Gtan -Slightsteelblue \
              -A8000 -Bg30 -W0.2p,gray40 -N1/0.2p,gray60
    gmt plot -W1.2p,red2 <<'BOX'
25 39
31 39
31 42
25 42
25 39
BOX
  gmt inset end

gmt end

echo "wrote ${OUT}.pdf and ${OUT}.png"
