#!/usr/bin/env python3
"""
Listing (siteresp): 1-D linear site-amplification transfer function.

Extracted verbatim from the source-code listing (lst:siteresp) of the
manuscript "Soil amplification and collapse screening in Istanbul".
This is the code as documented in the paper; the structural/site
listings (siteresp, mdof, modal) are the representative reference
implementations described there. Verify paths and parameters against
your local environment before running.

Description (from the listing caption):
One-dimensional equivalent-linear site amplification: the transfer function of a damped soil layer over elastic bedrock, used to derive the amplification factors and site periods of the Istanbul profiles.
"""

import numpy as np

def site_amplification(Vs, H, xi=0.05, rho_s=1900.0,
                       Vs_b=760.0, rho_b=2200.0,
                       f=np.linspace(0.1, 15.0, 400)):
    """Linear transfer function |F(f)| of a damped soil layer of
    thickness H (m) over elastic bedrock (Kramer, 1996)."""
    w        = 2*np.pi*f
    Vs_star  = Vs*(1 + 1j*xi)               # complex (damped) shear-wave velocity
    k        = w/Vs_star                     # complex wavenumber in the layer
    alpha    = (rho_s*Vs)/(rho_b*Vs_b)       # soil/bedrock impedance ratio
    F        = 1.0/(np.cos(k*H) + 1j*alpha*np.sin(k*H))
    return f, np.abs(F)

# Soft Marmara basin column (class D-E) vs. stiff shallow reference (class B)
f, A_soft  = site_amplification(Vs=200.0, H=120.0)
f, A_stiff = site_amplification(Vs=600.0, H=30.0)
Ts = 4*120.0/200.0                           # fundamental site period (s)
print(f"site period Ts = {Ts:.2f} s")
print(f"peak amplification soft  = {A_soft.max():.2f} at {f[A_soft.argmax()]:.2f} Hz")
print(f"peak amplification stiff = {A_stiff.max():.2f}")
