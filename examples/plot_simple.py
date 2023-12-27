"""
``PyPSG``
=========

A Python wrapper for the Planetary Spectrum Generator.

The goal of this package is to make PSG more accessible to
new users, but still be powerfull enough that expert users
will find it usefull.

In the simplest use case, users can create a PSG config file from scratch
using the ``PyConfig`` class.
"""

import pypsg

cfg = pypsg.cfg.PyConfig(
    target=pypsg.cfg.Target(object='Exoplanet',name='Proxima Cen b')
    )
print(cfg.content)

#%%
# Get the rad file
# ----------------
psg = pypsg.APICall(
        cfg=cfg,
        output_type='rad',
    )
response = psg()

#%%
# Look at the rad file
# --------------------
rad = response.rad

print(rad)