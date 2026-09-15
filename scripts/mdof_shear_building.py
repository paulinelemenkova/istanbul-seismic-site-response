#!/usr/bin/env python3

import numpy as np
from scipy.linalg import eigh

def building_descriptors(N, m, k, h_s):
    """Dynamic descriptors of an N-storey lumped-mass shear building:
    building height, modal periods and effective modal-mass fractions
    from the generalised eigenproblem (eq:mdof, eq:eig)."""
    M = m*np.eye(N)                          # lumped storey masses
    K = np.zeros((N, N))                      # tridiagonal shear stiffness
    for i in range(N):
        K[i, i] += k
        if i + 1 < N:
            K[i, i+1] -= k; K[i+1, i] -= k; K[i+1, i+1] += k
    w2, Phi = eigh(K, M)                      # generalised eigenproblem
    omega = np.sqrt(w2); T = 2*np.pi/omega    # modal periods (T[0] = fundamental)
    Delta = np.ones(N)                        # earthquake influence vector
    meff = np.array([(Phi[:, j] @ M @ Delta)**2 / (Phi[:, j] @ M @ Phi[:, j])
                     for j in range(N)])      # effective modal masses
    return N*h_s, T, meff/(N*m)

# Representative 10-storey Istanbul RC shear building (Table storey_properties)
H, T, mass_frac = building_descriptors(N=10, m=5.0e5, k=2.5e8, h_s=3.2)
print(f"building height H   = {H:.1f} m")
print(f"fundamental period  = {T[0]:.2f} s")
print(f"1st-mode mass frac  = {100*mass_frac[0]:.1f} %")
