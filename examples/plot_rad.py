"""
Plot a rad file
===============

Get a rad file from PSG and plot it.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u

from pypsg.cfg.config import PyConfig
from pypsg import APICall
from pypsg import settings
from pypsg.cfg.base import Table

try:
    CFG_PATH = Path(__file__).parent / 'psg_cfg.txt'
except NameError:
    CFG_PATH = Path('psg_cfg.txt')

settings.save_settings(url=settings.INTERNAL_PSG_URL)
settings.reload_settings()

#%%
# Read the file
# ------------

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

spec = rad.target

plt.plot(spec.spectral_axis,spec.flux)
plt.xlabel(spec.spectral_axis.unit)
plt.ylabel(spec.flux.unit)
0