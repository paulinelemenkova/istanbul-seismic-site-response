#!/usr/bin/env python3
"""
Listing (modal): response-spectrum modal analysis.

Extracted verbatim from the source-code listing (lst:modal) of the
manuscript "Soil amplification and collapse screening in Istanbul".
This is the code as documented in the paper; the structural/site
listings (siteresp, mdof, modal) are the representative reference
implementations described there. Verify paths and parameters against
your local environment before running.

Description (from the listing caption):
Response-spectrum modal analysis with an EC8/TBEC-type design spectrum, applied to a representative Istanbul shear-building model (Python translation of the mini-project routine).
"""

import numpy as np
from scipy.linalg import eigh

def design_spectrum(T, ag=1.0, S=1.2, TB=0.1, TC=0.3, TD=1.5):
    """EC8/TBEC-2018 elastic pseudo-acceleration spectrum, Eq. (ec8)."""
    if T < TB:        return ag*S*(1 + 1.5*T/TB)
    elif T < TC:      return ag*S*2.5
    elif T < TD:      return ag*S*2.5*(TC/T)
    else:             return ag*S*2.5*(TC*TD/T**2)

# Two-storey shear model: lumped mass m, storey stiffness k
m, k = 1.0e3, 1.0e6
M = np.array([[m, 0.0], [0.0, m]])
K = np.array([[2*k, -k], [-k, k]])
Delta = np.array([1.0, 1.0])                  # earthquake direction vector

w2, Phi = eigh(K, M)                           # generalised eigenproblem (eq:eig)
omega = np.sqrt(w2); freq = omega/(2*np.pi); T = 1.0/freq

dep = np.zeros(2); Vb = 0.0
for i in range(2):
    phi = Phi[:, i] / Phi[1, i]                # normalise on top storey
    L     = phi @ M @ Delta
    mmod  = phi @ M @ phi
    r     = L/mmod                             # modal participation factor
    meff  = L**2/mmod                          # effective modal mass
    Sa    = design_spectrum(T[i])
    depm  = Sa/omega[i]**2 * r * phi           # modal displacements (eq:spectra)
    dep   = np.sqrt(dep**2 + depm**2)          # SRSS over modes
    Vb    = np.sqrt(Vb**2 + (Sa*meff)**2)      # SRSS base shear
    print(f"mode {i+1}: f={freq[i]:.3f} Hz, r={r:.3f}, meff={meff:.1f} kg, Sa={Sa:.3f}")
print("SRSS top displacement:", dep, "  base shear:", Vb)
