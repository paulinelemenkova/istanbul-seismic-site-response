#!/usr/bin/env bash
set -e

R=26.5/30.0/40.08/41.32
J=M17c

gmt set FONT_ANNOT_PRIMARY 9p FONT_LABEL 10p FONT_TITLE 13p \
        MAP_FRAME_TYPE plain MAP_FRAME_PEN 0.9p \
        MAP_GRID_PEN_PRIMARY 0.25p,gray70,4_3 \
        MAP_TICK_LENGTH_PRIMARY 3p FORMAT_GEO_MAP ddd:mmF

DEM=""
for f in marmara_dem.nc marmara_dem.tif marmara_srtm.tif; do
  [ -f "$f" ] && DEM="$f" && break
done
if [ -z "$DEM" ]; then
  if gmt grdcut @earth_relief_03s -R$R -Gmarmara_dem.nc 2>/dev/null; then
    DEM=marmara_dem.nc
  fi
fi

gmt begin fig09_seismicity pdf,png
  gmt basemap -R$R -J$J -B0.5g0.5 -BWSen

  if [ -n "$DEM" ]; then
    gmt grdgradient "$DEM" -A300 -Ne0.7 -Gintens.nc
    gmt makecpt -Cgray -T-6000/3000 -H > relief_gray.cpt
    gmt grdimage "$DEM" -Iintens.nc -Crelief_gray.cpt
    gmt coast -Di -Slightblue@30 -W0.4p,gray45 -N1/0.5p,gray55 -A20
  else
    gmt coast -Di -Ggray88 -Slightblue -W0.4p,gray45 -N1/0.5p,gray55 -A20
  fi

  gmt plot faults_marmara.gmt -W1.1p,red3

  gmt makecpt -Cjet -T0/25/1 -H > depth.cpt
  fg=$(grep -E '^[0-9]' depth.cpt | tail -1 | awk '{print $4}')
  sed -i "s|^F.*|F\t$fg|" depth.cpt

  gmt plot epicentres.txt -Sc -Cdepth.cpt -W0.12p,gray35 -t35

  gmt meca marmara_meca.txt -Sa0.32c -Cdepth.cpt -W0.25p,black -L0.25p,black

  gmt text -F+f+j -Gwhite@25 -C18%/18% <<'TXT'
27.55 40.40 10p,Helvetica-Oblique,navy CM Sea of Marmara
29.02 41.18 11p,Helvetica-Bold,black CM Istanbul
28.52 41.08 8.5p,Helvetica-Oblique,gray20 CM Central Basin
27.90 41.08 8.5p,Helvetica-Oblique,gray20 CM Kumburgaz Basin
29.28 40.98 8.5p,Helvetica-Oblique,gray20 CM Cinarcik Basin
29.58 40.49 8.5p,Helvetica-Oblique,gray20 CM Gulf of Izmit
TXT
  gmt text -F+f9p,Helvetica-BoldOblique,red3+a-5+jCM -Gwhite@25 -C12%/12% <<'TXT'
27.55 40.74 North Anatolian Fault
TXT

  gmt colorbar -Cdepth.cpt -DjBL+w4.6c/0.32c+o0.7c/0.7c+h+ml \
               -Bxa5f1+l"Focal depth (km)" -F+gwhite@8+p0.4p,gray50+c2p

  gmt legend -DjTR+w2.7c+o0.25c/0.25c -F+gwhite@10+p0.5p,gray50+c3p <<'LEG'
H 9p,Helvetica-Bold Magnitude M@-L@-
G 0.06c
S 0.30c c 0.046c gray75 0.2p,gray30 0.62c 2
S 0.30c c 0.150c gray75 0.2p,gray30 0.62c 4
S 0.30c c 0.254c gray75 0.2p,gray30 0.62c 6
LEG

  gmt basemap -LjBR+w50k+o0.7c/0.7c+f+u --FONT_LABEL=8p --FONT_ANNOT_PRIMARY=8p
gmt end
