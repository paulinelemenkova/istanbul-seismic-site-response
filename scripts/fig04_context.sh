#!/usr/bin/env bash
set -e

REG=-R26/31.3/39.6/41.5
PROJ=-JM16c
OUT=fig04_context

awk -F, 'NR>1 {lat=$5+0; lon=$6+0; mag=$8+0;
        if(lon>=26 && lon<=31.3 && lat>=39.6 && lat<=41.5 && mag>0){
            s=0.045+0.075*(mag-1.5); if(s>0.42)s=0.42; if(s<0.05)s=0.05;
            printf "%.4f %.4f %.2f %.3f\n", lon, lat, mag, s}}' \
    IEB_export_1_.csv > seismicity.txt

if [ ! -f flt4_2l.gmt ] && [ -f flt4_2l.shp ]; then
    ogr2ogr -t_srs EPSG:4326 -f OGR_GMT flt4_2l.gmt flt4_2l.shp
fi

gmt set FORMAT_GEO_MAP=dddF \
        MAP_FRAME_TYPE=plain MAP_FRAME_PEN=0.9p,gray25 \
        MAP_TICK_PEN_PRIMARY=0.7p,gray25 \
        MAP_GRID_PEN_PRIMARY=0.35p,white \
        FONT_TITLE=15p,Helvetica-Bold,black \
        FONT_ANNOT_PRIMARY=8p,Helvetica,gray15 \
        FONT_LABEL=9p,Helvetica,gray15

gmt begin ${OUT} pdf,png E400

  gmt coast $REG $PROJ -Df \
      -G244/238/224 -Slightsteelblue@30 \
      -W0.3p,gray40 -N1/0.5p,gray55,- -Ia/0.3p,steelblue

  gmt makecpt -Cseis -T1.5/5/0.5 -Z -I -H > seis.cpt
  gmt plot seismicity.txt -i0,1,2,3 -Sc -Cseis.cpt -W0.15p,gray30 -t25

  [ -f flt4_2l.gmt ] && gmt plot flt4_2l.gmt -W0.6p,gray20
  gmt plot secondary_faults.txt -W1.4p,firebrick,4_2:0p
  gmt plot main_marmara_fault.txt -W2.4p,red2
  gmt plot main_marmara_fault.txt -W0.6p,white,.

  gmt plot hist_eq.txt -i0,1,2+s0.115 -Sa -Ggold -W0.9p,black
  gmt text hist_labels.txt -F+f8p,Helvetica-Bold,black -Gwhite@25 -W0.2p,gray70

  gmt plot stations.txt -St0.28c -Gdodgerblue3 -W0.4p,white

  gmt plot -Sv0.5c+ea+h0.5 -Gorange -W2.4p,orange <<'EOF'
29.65 39.84 192 2.8c
EOF
  gmt text -N -F+f8.5p,Helvetica-BoldOblique,gray20+jRM <<'EOF'
29.80 39.74 ~20-25 mm/yr
EOF
  gmt text -N -F+f10p,Helvetica-Bold,gold2+jCM <<'EOF'
27.00 41.37 E U R A S I A N   P L A T E
EOF
  gmt text -N -F+f10p,Helvetica-Bold,gold2+jCM <<'EOF'
30.35 39.76 A N A T O L I A N   B L O C K
EOF

  gmt text -N -F+f12p,Helvetica-Oblique,white+jCM <<'EOF'
28.30 40.62 Sea of Marmara
30.55 41.40 Black Sea
EOF
  gmt text -N -F+f12p,Helvetica-Oblique,white+a90+jCM <<'EOF'
26.13 40.12 Aegean Sea
EOF
  gmt text -N -F+f7.5p,Helvetica-Oblique,white+jCM <<'EOF'
26.55 40.55 Gulf of Saros
29.70 40.755 Gulf of Izmit
EOF

  gmt text -N -F+f8.5p,Helvetica-Bold,black+jBL -D0.14c/0.14c -Gwhite@30 <<'EOF'
29.00 41.03 Istanbul
29.97 40.79 Izmit
27.51 40.99 Tekirdag
27.97 40.37 Bandirma
29.06 40.20 Bursa
29.28 40.67 Yalova
EOF

  gmt basemap -Bxa1f0.5g1 -Bya0.5f0.25g1 -BWeSn+t"Seismotectonic context of the Istanbul-Marmara region"

  gmt basemap -LjBL+w50k+o0.7c/0.7c+f+l"km"+u --FONT_LABEL=8p,Helvetica,black
  gmt basemap -TdjBL+w0.9c+o1.0c/1.65c+f2+l,,,N --FONT_TITLE=9p

  gmt colorbar -Cseis.cpt -DJML+w6.6c/0.32c+o1.6c/0c+ml+e \
      -Bxa1f0.1+l"Instrumental seismicity: magnitude M" \
      --FONT_ANNOT_PRIMARY=7.5p --FONT_LABEL=8p

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
