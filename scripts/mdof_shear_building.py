#!/usr/bin/env python3

import numpy as np
from scipy.linalg import eigh

def building_descriptors(N, m, k, h_s):
    M = m*np.eye(N)
    K = np.zeros((N, N))
    for i in range(N):
        K[i, i] += k
        if i + 1 < N:
            K[i, i+1] -= k; K[i+1, i] -= k; K[i+1, i+1] += k
    w2, Phi = eigh(K, M)
    omega = np.sqrt(w2); T = 2*np.pi/omega
    Delta = np.ones(N)
    meff = np.array([(Phi[:, j] @ M @ Delta)**2 / (Phi[:, j] @ M @ Phi[:, j])
                     for j in range(N)])
    return N*h_s, T, meff/(N*m)

H, T, mass_frac = building_descriptors(N=10, m=5.0e5, k=2.5e8, h_s=3.2)
print(f"building height H   = {H:.1f} m")
print(f"fundamental period  = {T[0]:.2f} s")
print(f"1st-mode mass frac  = {100*mass_frac[0]:.1f} %")
