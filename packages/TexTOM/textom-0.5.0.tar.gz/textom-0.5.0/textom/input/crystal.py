import numpy as np
## Define diffraction-related parameters:
# x-ray energy in keV
E_keV = 15.2
# q range for fitting
q_range = (10,35)
# q = np.linspace(10, 35, num=50)
# # azimutal range for fitting
# n_chi = 120
# chi = np.linspace( 0, 2*np.pi, n_chi, endpoint=False) + 2*np.pi/n_chi/2
# path to crystal cif file
cifPath = 'analysis/BaCO3.cif'
# crystal size (repeat unit cell along each axis)
crystalsize = (15,15,15)
# angular sampling
sampling = 'cubochoric' # or 'simple' (legacy)
# angular sampling resolution
dchi = 2*np.pi / 120
