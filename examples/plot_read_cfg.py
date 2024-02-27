"""
Read a PSG configuration file
=============================

This example shows how to read a configuration file
and plot the layers.
"""
from typing import List
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from pypsg.cfg.config import PyConfig, BinConfig
from pypsg.cfg.base import Profile

try:
    CFG_PATH = Path(__file__).parent / 'psg_cfg.txt'
except NameError:
    CFG_PATH = Path('psg_cfg.txt')

#%%
# Read the file
# -------------

cfg = BinConfig.from_file(CFG_PATH)

print(cfg.content)

#%%
# Create a PyConfig object
# ------------------------

pycfg = PyConfig.from_binaryconfig(cfg)

#%%
# Plot the layers

profs:List[Profile] = pycfg.atmosphere.profile.value
pdict = {prof.name:prof.dat for prof in profs}

plt.plot(pdict[Profile.TEMPERATURE], pdict[Profile.PRESSURE])
plt.xlabel('Temperature')
plt.ylabel('Pressure')
plt.yscale('log')
plt.ylim(*np.flip(plt.ylim()))


