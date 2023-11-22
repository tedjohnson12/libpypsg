"""
Read a PSG configuration file
=============================

This example shows how to read a configuration file
and plot the layers.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from pypsg.cfg.config import PyConfig, BinaryConfig

CFG_PATH = Path(__file__).parent / 'psg_cfg.txt'

#%%
# Read the file
# ------------

cfg = BinaryConfig.from_file(CFG_PATH)

print(cfg.content)

#%%
# Create a PyConfig object
# ------------------------

pycfg = PyConfig.from_binaryconfig(cfg)

#%%
# Plot the layers

profs = pycfg.atmosphere.profile.raw_value

plt.plot(profs[1].dat,profs[0].dat)
plt.xlabel('Temperature')
plt.ylabel('Pressure')
plt.yscale('log')
plt.ylim(*np.flip(plt.ylim()))


