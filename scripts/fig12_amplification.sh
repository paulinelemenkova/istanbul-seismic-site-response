#!/bin/sh
# ============================================================================
# fig12_amplification — equivalent-linear site-amplification field over the
#                       Istanbul–Marmara area (GMT 6.x, modern mode)
# ----------------------------------------------------------------------------
# WHAT CHANGED relative to the previous version of this script, and why
# ----------------------------------------------------------------------------
# The previous script did NOT plot site amplification. It built the field from
# topography alone:
#
#     s   = softness index from slope          (flat -> 1, steep -> 0)
#     sed = clip((50 - elevation)/50, 0, 1)    ("sediment-thickness proxy")
#     F   = 1 + 0.95*(0.6*s + 0.4*sed),  land-mean RESCALED to 1.34,
#           clipped to [1.0, 1.85]
#
# That is an ad-hoc linear blend of two topographic indices, not an
# amplification model, and rescaling the mean onto the manuscript's quoted 1.34
# made the reported statistic circular. It also produced a drainage-network
# texture rather than a basin pattern, so the Results claim that the elevated
# interior lies below 1.2 was not supported by the map.
#
# This version computes F from the stated physics and from real input grids:
#
#     F = (V_ref / Vs30)^m           Borcherdt (1994) site-amplification form,
#                                    V_ref = 760 m/s (engineering bedrock, the
#                                    NEHRP B/C boundary used by the Istanbul
#                                    microzonation)
#
# with Vs30 read from the USGS global hybrid Vs30 mosaic (Heath et al. 2020) —
# the grid named in Table 2 of the manuscript — cut to this window. No values
# are invented, no mean is forced, and no arbitrary clip is applied: the script
# prints the statistics that actually result so they can be compared with the
# text rather than imposed on it.
#
# REQUIRED INPUT
#   vs30.nc       Vs30 (m/s) on this window. From the USGS mosaic:
#                     gmt grdcut global_vs30.grd -R$R -Gvs30.nc
#   mmf_trace.txt Main Marmara Fault trace, "lon lat" per line. Export the same
#                 geometry used in Figure 10 rather than re-typing it: the old
#                 inline nine-vertex polyline was a hand sketch and did not
#                 match the database traces drawn elsewhere in the paper.
#
# OPTIONAL INPUT
#   topo.nc       relief for the hillshade. If absent the map is drawn flat;
#                 the coastline no longer depends on it (GSHHG is used).
#
# The script FAILS if a required grid is missing. It will not substitute a
# synthetic field, because a figure that silently differs from the manuscript
# is worse than no figure.
#
# Outputs: fig12_amplification.pdf + fig12_amplification.png
# ============================================================================
set -e

R=27.8/30.0/40.55/41.3          # Istanbul–Marmara window
VREF=760                        # engineering-bedrock velocity, m/s
MA=0.35                         # Borcherdt (1994) short-period exponent.
                                # SET THIS to the value used in Section 3:
                                # Borcherdt tabulates ma by input level
                                # (~0.35 at 0.1 g, falling as soil yields).
                                # It is a parameter of the model, not a knob to
                                # be tuned until the mean matches the text.

# LAYOUT_CHECK=1 draws the map furniture without the raster, so label placement
# can be verified when the input grids are not to hand. It is a diagnostic
# mode: the output is not the figure.
: "${LAYOUT_CHECK:=0}"

if [ "$LAYOUT_CHECK" != "1" ]; then
  [ -f vs30.nc ]       || { echo "ERROR: vs30.nc missing (see REQUIRED INPUT)"; exit 1; }
  [ -f mmf_trace.txt ] || echo "WARNING: mmf_trace.txt missing - fault overlay omitted"

  # --------------------------------------------------------------------------
  # 1. AMPLIFICATION  F = (V_ref/Vs30)^m   — Borcherdt (1994)
  # --------------------------------------------------------------------------
  gmt grdmath $VREF vs30.nc DIV $MA POW = amp.nc

  # Mask the sea: the mosaic assigns a nominal 600 m/s over water, which is not
  # a site condition and must not be shaded as one.
  INC=$(gmt grdinfo vs30.nc -Cn -o7)          # match the Vs30 posting exactly
  gmt grdlandmask -R$R -I$INC -Df -N0/1 -Glandmask.nc
  gmt grdmath amp.nc landmask.nc 0 NAN MUL = amp.nc

  echo "--- amplification statistics actually obtained (land only) ---"
  gmt grdinfo amp.nc -L2 | grep -E "z_min|mean|stdev|median" || true
  echo "--- compare these with the values quoted in the Results text ---"
fi

# ----------------------------------------------------------------------------
# 2. House style
# ----------------------------------------------------------------------------
# GMT's "Helvetica" is URW Nimbus Sans, the manuscript's mandated face.
gmt set FONT_TITLE=13p,Helvetica-Bold,black FONT_LABEL=10p,Helvetica,black \
        FONT_ANNOT_PRIMARY=9p,Helvetica,black MAP_FRAME_PEN=0.8p,black \
        MAP_FRAME_TYPE=plain MAP_TICK_LENGTH_PRIMARY=0.12c \
        MAP_GRID_PEN_PRIMARY=0.25p,white FORMAT_GEO_MAP=ddd:mmF \
        MAP_TITLE_OFFSET=0.3c

# CPT choice. Requested: seis or wysiwyg (see the note below on what each
# costs). cpt_tools.assess reports:
#   gmt/seis     diverging, L* 26-97 -- an ordered ramp, but its lightness rises
#                to a light centre and falls again, so two different values of F
#                print as the same grey and the pale band reads as a boundary
#                where the data have none.
#   gmt/wysiwyg  UNSUITABLE -- a 20-colour categorical set whose lightness
#                doubles back four times. It encodes categories, not a
#                continuous field, and cannot be read in greyscale at all.
# seis is therefore used here as the lesser of the two. Set CPT=lajolla (with
# -I) or CPT=roma for a scale whose ordering survives print.
CPT=${CPT:-seis}
if [ "$LAYOUT_CHECK" != "1" ]; then
  CPTMIN=$(gmt grdinfo amp.nc -Cn -o4 | awk '{printf "%.2f", int($1*20)/20}')
  CPTMAX=$(gmt grdinfo amp.nc -Cn -o5 | awk '{printf "%.2f", (int($1*20)+1)/20}')
  case "$CPT" in
    # seis runs red at low z and blue at high z; inverted so that high
    # amplification reads hot, as in the previous version of this figure and as
    # a hazard map is conventionally read.
    lajolla|seis) gmt makecpt -C$CPT -I -T$CPTMIN/$CPTMAX/0.01 -Z > amp.cpt ;;
    *)            gmt makecpt -C$CPT    -T$CPTMIN/$CPTMAX/0.01 -Z > amp.cpt ;;
  esac
  echo "colour scale set to $CPTMIN - $CPTMAX"
fi

# ----------------------------------------------------------------------------
# 3. FIGURE
# ----------------------------------------------------------------------------
gmt begin fig12_amplification pdf,png E300

  gmt basemap -R$R -JM17c \
    -B+t"Equivalent-linear site amplification, Istanbul-Marmara area"

  # sea, then the amplification field over land, then real GSHHG coastlines
  gmt coast -Slightsteelblue1 -Glightgray -Df
  if [ "$LAYOUT_CHECK" != "1" ]; then
    if [ -f topo.nc ]; then
      gmt grdgradient topo.nc -Nt1.2 -A315 -Gintensity.nc
      gmt grdimage amp.nc -Camp.cpt -Iintensity.nc -Q
    else
      gmt grdimage amp.nc -Camp.cpt -Q
    fi
  fi
  gmt coast -W0.5p,gray25 -Df

  # ---- Main Marmara Fault: real geometry, from file -------------------------
  if [ -f mmf_trace.txt ]; then
    gmt plot mmf_trace.txt -W1.8p,red3
    echo "28.50 40.795 Main Marmara Fault" | gmt text \
      -F+f9p,Helvetica-BoldOblique,red3+jLT+a-4 -Gwhite@35 -W0.2p,red3 -C12%/18%
  fi

  # ---- earthquakes ----------------------------------------------------------
  # The 1999 event is M_w 7.4, the value used in the manuscript body and in
  # Figure 6. The previous version labelled it 7.6 here and 7.4 there.
  cat > eqs.txt <<'EOF'
29.864 40.748 7.40
28.190 40.834 6.20
28.150 40.904 5.70
EOF
  gmt plot eqs.txt -Sa -i0,1,2+s0.11 -Gyellow -W0.6p,black
  # labels pushed clear of the fault line, the coast and the Gulf of Izmit name
  gmt text -F+f8p,Helvetica-Bold,black+jRB -Gwhite@30 -W0.15p,gray50 -C8%/12% -D-0.20c/0.10c <<'EOF'
28.150 40.904 2019 M5.7
EOF
  gmt text -F+f8p,Helvetica-Bold,black+jRM -Gwhite@30 -W0.15p,gray50 -C8%/12% -D-0.20c/0c <<'EOF'
28.190 40.834 2025 Silivri M6.2
EOF
  gmt text -F+f8p,Helvetica-Bold,black+jLB -Gwhite@30 -W0.15p,gray50 -C8%/12% <<'EOF'
29.700 40.640 1999 Izmit M@-w@-7.4
EOF

  # ---- soft-soil coastal districts: dots + single leader + one callout ------
  gmt plot -Sc0.09c -Gblack -W0.3p,white <<'EOF'
28.72 40.985
28.78 41.000
28.87 40.975
28.91 40.990
28.67 41.030
EOF
  gmt plot -W0.5p,gray35 <<'EOF'
28.80 40.975
28.80 40.800
EOF
  gmt text -F+f8p,Helvetica-Bold,black+jCB -Gwhite@15 -W0.2p,gray55 -C14%/18% <<'EOF'
28.80 40.788 Soft-soil coastal districts (high amplification):
EOF
  gmt text -F+f7.5p,Helvetica,black+jCT -Gwhite@15 -W0.2p,gray55 -C14%/18% <<'EOF'
28.80 40.780 Avcilar \267 Kucukcekmece \267 Bakirkoy \267 Zeytinburnu \267 Esenyurt
EOF

  # ---- cities, water bodies, local labels -----------------------------------
  gmt plot -Sc0.16c -Gyellow -W0.6p,black <<'EOF'
28.98 41.01
27.98 41.07
28.46 41.14
29.43 40.80
29.27 40.65
29.19 40.89
29.61 41.18
EOF
  gmt text -F+f8p,Helvetica-Bold,black+jLM -D0.16c/0c -Gwhite@30 -W0.15p,gray60 -C6%/10% <<'EOF'
28.98 41.01 Istanbul
27.98 41.07 Silivri
28.46 41.14 Catalca
29.43 40.80 Gebze
29.27 40.65 Yalova
29.19 40.89 Kartal
29.61 41.18 Sile
EOF
  # Princes' Islands note moved off the fault label
  echo "29.10 40.930 Princes' Is. (rock, low amplification)" | gmt text \
    -F+f8p,Helvetica-Oblique,navy+jLB -Gwhite@30 -C6%/10%
  gmt text -F+f9p,Helvetica-Oblique,steelblue4+jCM <<'EOF'
28.30 40.690 Sea of Marmara
29.72 40.880 Gulf of Izmit
29.55 41.255 Black Sea
EOF

  # ---- colour bar -----------------------------------------------------------
  if [ "$LAYOUT_CHECK" != "1" ]; then
    gmt colorbar -Camp.cpt -DJBC+o0/0.95c+w10c/0.34c+h \
      -Bxa0.1f0.05+l"Site-amplification factor @%1%F@%% = (760 / V@-s30@-)@+m@+" \
      --FONT_LABEL=10p --FONT_ANNOT_PRIMARY=8p
  fi

  # ---- frame, graticule, scale bar, north arrow -----------------------------
  gmt basemap -Bxa0.5f0.25g0.5 -Bya0.25f0.125g0.25 -BWSne \
    -LjBL+w50k+f+o0.6c/0.45c+u --FONT_LABEL=8p \
    -TdjTR+w0.8c+o0.35c/0.35c+f2+l,,,N

  # ---- credit line ----------------------------------------------------------
  gmt text -R0/10/0/10 -JX17c/1c -Y-2.55c -N -F+f7p,Helvetica,gray45+jLB <<'EOF'
0 0 Amplification: F = (760/V@-s30@-)@+m@+ after Borcherdt (1994); V@-s30@- from the USGS hybrid mosaic (Heath et al. 2020). Fault as Fig. 10; quakes KOERI.
EOF
gmt end
