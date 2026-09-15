#!/usr/bin/env python3

import warnings; warnings.filterwarnings('ignore')
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from pyproj import Transformer
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon as MplPoly
from matplotlib.lines import Line2D

LON0,LON1,LAT0,LAT1 = 26.0,31.0,39.5,42.0
T = Transformer.from_crs(4326,3857,always_xy=True)
def P(lon,lat):
    return T.transform(lon,lat)
X0,Y0 = P(LON0,LAT0); X1,Y1 = P(LON1,LAT1)

CMAP={
 'Q':'#faeeb0','N':'#fff24d','Pg':'#fdb45f','Cz':'#ffd27a','TK':'#d7de86',
 'K':'#8fcb66','J':'#52b7ce','Tr':'#8e66b0','Mz':'#79c892','D':'#cc9a52',
 'DS':'#d9c06a','C':'#7fb0a4','Pz':'#a8aa4d','Pzu':'#bcbd63','Pzl':'#a0c06c',
 'PzpCm':'#c77fa6','pCm':'#e673a6','Pzi':'#e2574e','CzMzi':'#f2728a','pCmi':'#b5392c',
 'Tv':'#ea6336','Czv':'#db4f4a','Pzm':'#c49ad0','Mzm':'#dcc0e0','MzPzm':'#ad86bc',
 'PzpCmm':'#8e6f9e','unk':'#d0d0d0',
}
SEA='#b3d7e8'; FAULTC='#d11500'
WATER={'H2O','Sea1','Sea2','Sea3','Sea4','Sea5','m','ice','oth'}

GEO=[('Q','Quaternary'),('N','Neogene'),('Pg','Paleogene'),('Cz','Cenozoic undiv.'),('TK','Tertiary\u2013Cretaceous'),
     ('K','Cretaceous'),('J','Jurassic'),('Tr','Triassic'),('Mz','Mesozoic undiv.'),('D','Devonian'),
     ('DS','Devonian\u2013Silurian'),('C','Carboniferous'),('Pz','Paleozoic undiv.'),('Pzu','Upper Paleozoic'),('Pzl','Lower Paleozoic'),
     ('PzpCm','Paleozoic\u2013Precambrian'),('pCm','Precambrian'),('Pzi','Paleozoic intrusive'),('CzMzi','Cz\u2013Mz intrusive'),('pCmi','Precambrian intrusive'),
     ('Tv','Tertiary volcanic'),('Czv','Cenozoic volcanic'),('Pzm','Paleozoic metamorphic'),('Mzm','Mesozoic metamorphic'),('MzPzm','Mz\u2013Pz metamorphic'),
     ('PzpCmm','Pz\u2013pCm metamorphic'),('unk','Undetermined')]

PRV_ORDER=['Thrace/Samsun','Kardiff/Menders Massif','Aegean',
           'Black Sea Deep-Water Basin','Carpathian-Balkanian Basin','Lesser Caucasus']
PRV_STYLE={'Thrace/Samsun':('/','#703388'),
           'Kardiff/Menders Massif':('\\','#146e4a'),
           'Aegean':('x','#9c4a1a'),
           'Black Sea Deep-Water Basin':('.','#16538c'),
           'Carpathian-Balkanian Basin':('+','#a5396d'),
           'Lesser Caucasus':('','#555555')}
PRV_SHORT={'Thrace/Samsun':'Thrace Basin','Kardiff/Menders Massif':'Kirklareli\u2013Menderes',
           'Aegean':'Aegean','Black Sea Deep-Water Basin':'Black Sea D.-W.',
           'Carpathian-Balkanian Basin':'Carpathian\u2013Balk.','Lesser Caucasus':'Lesser Caucasus'}

win=box(LON0,LAT0,LON1,LAT1)
def load(fn):
    g=gpd.read_file(fn).to_crs(4326)
    g=gpd.clip(g,win)
    return g.to_crs(3857)
geo=load('data/geo4_2l.shp')
prv=gpd.read_file('data/prv4_2l.shp').to_crs(4326)
prv=gpd.clip(prv,win).to_crs(3857)
try:
    flt=load('data/flt4_2l.shp')
except Exception:
    flt=None

fig=plt.figure(figsize=(21,17.01),dpi=200)
ax=fig.add_axes([0.060,0.112,0.892,0.700])
ax.set_xlim(X0,X1); ax.set_ylim(Y0,Y1); ax.set_aspect('auto')

for code,grp in geo.groupby('GLG'):
    col = SEA if code in WATER else CMAP.get(code,'#d0d0d0')
    grp.plot(ax=ax,facecolor=col,edgecolor='#6b6b6b',linewidth=0.12,zorder=1)

for nm in PRV_ORDER:
    sel=prv[prv['NAME']==nm]
    if len(sel)==0: continue
    htch,col=PRV_STYLE[nm]
    sel.plot(ax=ax,facecolor='none',edgecolor=col,hatch=htch if htch else None,
             linewidth=1.1,zorder=3,alpha=0.95)

if flt is not None and len(flt):
    flt.plot(ax=ax,color=FAULTC,linewidth=1.6,zorder=4)

lon_t=np.arange(26,32,1); lat_t=np.arange(39.5,42.01,0.5)
for lo in lon_t:
    x,_=P(lo,LAT0); ax.plot([x,x],[Y0,Y1],color='white',lw=0.8,ls=(0,(5,4)),zorder=2,alpha=0.85)
for la in lat_t:
    _,y=P(LON0,la); ax.plot([X0,X1],[y,y],color='white',lw=0.8,ls=(0,(5,4)),zorder=2,alpha=0.85)

CITIES=[('Edirne',26.56,41.68),('Kirklareli',27.22,41.74),('L\u00fcleburgaz',27.36,41.40),
        ('\u00c7orlu',27.80,41.16),('Silivri',28.25,41.07),('Tekirdag',27.51,40.98),
        ('Gebze',29.43,40.80),('Izmit',29.92,40.77),('Adapazari',30.54,40.78),
        ('Yalova',29.28,40.655),('Bandirma',27.97,40.35),('Bursa',29.06,40.19),
        ('\u00c7anakkale',26.41,40.15)]
for nm,lo,la in CITIES:
    x,y=P(lo,la)
    ax.plot(x,y,'o',ms=6,mfc='black',mec='black',zorder=6)
    ax.annotate(nm,(x,y),xytext=(9,4),textcoords='offset points',
                fontsize=15,weight='bold',zorder=7)

ix,iy=P(28.98,41.013)
ax.plot(ix,iy,marker='*',ms=26,mfc='white',mec='black',mew=1.6,zorder=8)
ax.annotate('Istanbul',(ix,iy),xytext=(15,6),textcoords='offset points',
            fontsize=21,weight='bold',zorder=8)

def sealab(txt,lo,la,size,col='#1f4e79',rot=0,ha='center'):
    x,y=P(lo,la)
    ax.text(x,y,txt,fontsize=size,style='italic',color=col,ha=ha,va='center',
            rotation=rot,zorder=7)
sealab('Sea of Marmara',28.1833,40.75,24)
sealab('Black Sea',29.25,41.3333,30)
sealab('Aegean Sea',26.12,40.02,22,rot=90)
sealab('Black Sea Deep-Water Basin',29.55,41.70,16,col='#2266aa',rot=0)

def prvlab(txt,lo,la,col,size=18,rot=0):
    x,y=P(lo,la); ax.text(x,y,txt,fontsize=size,style='italic',weight='bold',
                          color=col,ha='center',va='center',zorder=7,rotation=rot)
prvlab('Carpathian-Balkanian',26.95,41.83,'#a5396d',17)
prvlab('Thrace Basin',27.62,41.50,'#703388',19)
prvlab('Aegean',26.62,40.46,'#9c4a1a',17)
prvlab('Kirklareli-Menderes Massif',28.75,39.86,'#146e4a',19)

sb_lat=39.63; sb_lon0=30.30
dlon=50.0/(111.32*np.cos(np.radians(sb_lat)))
xs0,ysb=P(sb_lon0,sb_lat); xs1,_=P(sb_lon0+dlon,sb_lat)
bw=(xs1-xs0); bh=(Y1-Y0)*0.012
ax.add_patch(Rectangle((xs0-bw*0.08,ysb-bh*1.3),bw*1.16,bh*3.1,
             facecolor='#fff0f0',edgecolor='none',alpha=0.75,zorder=8))
for s in range(4):
    c='black' if s%2 else 'white'
    ax.add_patch(Rectangle((xs0+s*bw/4,ysb),bw/4,bh,facecolor=c,edgecolor='black',lw=0.8,zorder=9))
ax.text(xs0,ysb-bh*0.6,'0 km',fontsize=11.5,ha='center',va='top',zorder=9)
ax.text(xs1,ysb-bh*0.6,'50 km',fontsize=11.5,ha='center',va='top',zorder=9)

def lon_lab(d):  return f"{int(round(d))}\u00b0E"
def lat_lab(d):
    deg=int(d); mn=int(round((d-deg)*60))
    return f"{deg}\u00b0{mn:02d}'N"
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])

ax.add_patch(Rectangle((X0,Y0),X1-X0,Y1-Y0,fill=False,ec='black',lw=1.4,zorder=10))

def checker_h(y,flip):
    seg=np.arange(26,31.0001,0.25)
    th=(Y1-Y0)*0.010
    for i in range(len(seg)-1):
        xa,_=P(seg[i],LAT0); xb,_=P(seg[i+1],LAT0)
        c='black' if (i%2==0)^flip else 'white'
        ax.add_patch(Rectangle((xa,y),xb-xa,th if y>=Y1- th else th,
                     facecolor=c,edgecolor='black',lw=0.5,zorder=11,clip_on=False))
def checker_v(x):
    seg=np.arange(39.5,42.0001,0.25)
    tw=(X1-X0)*0.0065
    for i in range(len(seg)-1):
        _,ya=P(LON0,seg[i]); _,yb=P(LON0,seg[i+1])
        c='black' if i%2==0 else 'white'
        ax.add_patch(Rectangle((x,ya),tw,yb-ya,facecolor=c,edgecolor='black',
                     lw=0.5,zorder=11,clip_on=False))
th_h=(Y1-Y0)*0.010; tw_v=(X1-X0)*0.0065
checker_h(Y0,False)
checker_h(Y1-th_h,False)
checker_v(X0)
checker_v(X1-tw_v)

for lo in range(26,32):
    x,_=P(lo,LAT0); ax.text(x,Y0-(Y1-Y0)*0.022,lon_lab(lo),ha='center',va='top',fontsize=16)
for la in np.arange(39.5,42.01,0.5):
    _,y=P(LON0,la); ax.text(X0-(X1-X0)*0.006,y,lat_lab(la),ha='right',va='center',fontsize=16)

pax=fig.add_axes([0.052,0.828,0.900,0.162]); pax.set_xlim(0,1); pax.set_ylim(0,1); pax.axis('off')
pax.add_patch(FancyBboxPatch((0.003,0.02),0.994,0.96,
              boxstyle='round,pad=0.004,rounding_size=0.02',
              fc='none',ec='#5a5a5a',lw=1.4,mutation_aspect=0.17,zorder=0))
pax.text(0.5,0.915,'Generalized geology of the Marmara region   (USGS, 1:5\u202f000\u202f000)',
         ha='center',va='center',fontsize=23,weight='bold')
pax.plot([0.02,0.98],[0.825,0.825],color='#999',lw=0.8)
ncol=5; colw=1.0/ncol; xpad=0.012; sw=0.020
top=0.735; rowh=0.108
ents=[(c,CMAP[c],lab,'box') for c,lab in GEO]+[('','','Water bodies / sea','water'),('','','Faults','line')]
for i,(code,col,lab,kind) in enumerate(ents):
    c=i%ncol; r=i//ncol; xx=c*colw+xpad; yy=top-r*rowh
    if kind=='line':
        pax.plot([xx,xx+sw],[yy,yy],color=FAULTC,lw=2.6)
    else:
        fc=SEA if kind=='water' else col
        pax.add_patch(Rectangle((xx,yy-0.034),sw,0.068,facecolor=fc,edgecolor='#555',lw=0.6))
    tcode=f"$\\it{{{code}}}$ " if code else ""
    pax.text(xx+sw+0.006,yy,tcode+lab,fontsize=13.5,va='center')

pax.plot([0.02,0.98],[0.150,0.150],color='#999',lw=0.8)
pax.text(0.006,0.075,'Geologic\nprovinces:',fontsize=12.5,weight='bold',va='center',linespacing=0.95)
slot0=0.092; slotw=(0.972-slot0)/6.0
for j,nm in enumerate(PRV_ORDER):
    htch,col=PRV_STYLE[nm]; px=slot0+j*slotw
    pax.add_patch(Rectangle((px,0.046),0.020,0.058,facecolor='none',edgecolor=col,
                  hatch=(htch*2 if htch else None),lw=0.0))
    pax.add_patch(Rectangle((px,0.046),0.020,0.058,facecolor='none',edgecolor=col,lw=1.0))
    pax.text(px+0.025,0.075,PRV_SHORT[nm],fontsize=11.5,va='center')

rax=fig.add_axes([0.060,0.038,0.30,0.020]); rax.set_xlim(0,11); rax.set_ylim(0,1); rax.axis('off')
ramp=['Q','N','Pg','K','J','Tr','D','C','Pz','PzpCm','pCm']
for k,code in enumerate(ramp):
    rax.add_patch(Rectangle((k,0),1,1,facecolor=CMAP[code],edgecolor='white',lw=0.7))
rax.text(0,-0.5,'younger',fontsize=14,ha='left',va='top')
rax.text(11,-0.5,'older',fontsize=14,ha='right',va='top')
fig.text(0.060,0.066,'Geologic age',fontsize=15,weight='bold')

fig.text(0.948,0.049,'USGS OFR 97-470I \u00b7 generalized geology, faults & geologic provinces '
         'of Europe/Turkey \u00b7 geopandas / matplotlib',
         fontsize=15,color='#9a9a9a',ha='right',va='center')

fig.savefig('fig05_geology.pdf',facecolor='white')
fig.savefig('fig05_geology.png',dpi=200,facecolor='white')
print('saved fig05_geology.pdf / .png')
