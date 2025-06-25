"""
Plot a rad file
===============

Get a rad file from PSG and plot it.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u

from libpypsg.cfg.config import PyConfig
from libpypsg import APICall
from libpypsg import docker
from libpypsg.cfg.base import Table

try:
    CFG_PATH = Path(__file__).parent / 'psg_cfg.txt'
except NameError:
    CFG_PATH = Path('psg_cfg.txt')
    
docker.set_url_and_run()


#%%
# Read the file
# -------------

pycfg = PyConfig.from_file(CFG_PATH)

#%%
# Examine the cfg
# ---------------
# For fun

print(f'This config is looking at a {pycfg.target.object.value} object')
print(f'It is called {pycfg.target.name.value}')
print(f'It is {pycfg.geometry.observer_altitude.value} away.')

print(f'We will observe from {pycfg.telescope.range1.value} to {pycfg.telescope.range2.value}.')
print(f'The dark current is {pycfg.noise.dark_current.value}. Let\'s change it.')
x = np.linspace(1,20,10)*u.um
y = (np.sin((x/(3*u.um)).to_value(u.dimensionless_unscaled))+1)*pycfg.noise.dark_current.value
pycfg.noise.dark_current = Table(x,y)

print('Now the dark current is:')
print(pycfg.noise.dark_current.asbytes.decode('utf-8'))

plt.plot(x,y)
plt.xlabel(f'Wavelength ({x.unit})')
plt.ylabel(f'Dark current ({y.unit})')



#%%
# Run PSG
# -------

psg = APICall(pycfg,'rad')
rad = psg().rad

#%%
# Read the response
# -----------------

wl = rad.wl
flux = rad['Total']
plt.plot(wl,flux)
plt.xlabel(wl.unit)
plt.ylabel(flux.unit)
