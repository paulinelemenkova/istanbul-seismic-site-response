#!/usr/bin/env python3
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
