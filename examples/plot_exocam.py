"""
Work with an ExoCAM GCM
=======================

Learn how to use the ``pypsg.globes`` ExoCAM module. 


To get started, install ``pypsg``:

.. code-block:: bash

    pip install pypsg

It would also be beneficial to have PSG installed with docker.
"""

from pathlib import Path
from netCDF4 import Dataset
from cartopy import crs as ccrs
from astropy import units as u
import matplotlib.pyplot as plt
from pypsg.globes.exocam import exocam_to_pygcm, download_exocam_test_data
from pypsg import PyConfig, APICall
from pypsg.cfg import models
from pypsg.docker import set_url_and_run
from pypsg.units import resolving_power

TEST_PATH = download_exocam_test_data(rewrite=False) # Change this to the path of your dataset

set_url_and_run() # this will run PSG if it is installed. Otherwise it will change your url setting to `psg.gsfc.nasa.gov`.

#%%
# Read the file
# -------------

data = Dataset(TEST_PATH) # remember to close later.

#%%
# Convert to PyGCM
# ----------------

gcm = exocam_to_pygcm(
    data=data,                  # the GCM dataset
    itime=0,                    # the time index
    molecules=['H2O'],          # the molecule names
    aerosols=['Water'],         # the aerosol names
    background='N2',            # the background gas
    lon_start=0.,               # the longitude of the first pixel, optional
    lat_start=-90.,             # the latitude of the first pixel, optional (probably should never change)
    mean_molecular_mass=28.     # the mean molecular mass of the atmosphere. This is necessary if you have water.
)

data.close()

print(type(gcm))

#%%
# Have some fun with the GCM
# --------------------------
#
proj = ccrs.Mollweide(
                central_longitude=180)
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, projection=proj)
lats = gcm.lats
lons = gcm.lons
temperature = gcm.tsurf.dat.to_value(u.K).T
im = ax.pcolormesh(lons, lats, temperature, transform=ccrs.PlateCarree(),cmap='viridis')
fig.colorbar(im,ax=ax,label='T (K)',orientation='vertical')

#%%
# Set some other parameters
# -------------------------
#
# You can also read in a file and only change the ones you are interested in.
# This is just a very comprehensive example.

target = models.Target( # Most of these fields are optional
    object='Exoplanet',
    name='Proxima Cen b',
    diameter=2*u.R_earth,
    gravity=1*u.M_earth,
    star_distance=0.04856*u.au,
    star_velocity=0.00124*u.km/u.s,
    solar_longitude=0.*u.deg,
    solar_latitude=0.*u.deg,
    season=90*u.deg,
    star_temperature=2900.0*u.K,
    star_type='M',
    star_radius=0.14*u.R_sun,
    star_metallicity=0.0,
    obs_longitude=36.16*u.deg,
    obs_latitude=0.*u.deg,
    obs_velocity=0.499*u.km/u.s,
    period=11.1868*u.day,
    )

geometry = models.Observatory(
    observer_altitude=1.3*u.pc,
    stellar_type='M',
)

atmosphere = models.EquilibriumAtmosphere() # This will get changed by the GCM

generator = models.Generator(
    resolution_kernel=True,
    gas_model=True,
    continuum_model=True,
    continuum_stellar=True,
    apply_telluric_noise=True,
    apply_telluric_obs=False,
    rad_units=u.Unit('W m-2 um-1'),
    log_rad=False,
    gcm_binning=40, # Change this if you are doing real science
)

telescope = models.SingleTelescope(
    aperture=2*u.m,
    zodi=1.0,
    fov=5*u.arcsec,
    range1=1*u.um,
    range2=18*u.um,
    resolution=50.*resolving_power,
)

noise = models.CCD(
    read_noise=10*u.electron,
    dark_current=100*u.electron/u.s,
    thoughput=1.0,
    emissivity=0.1,
    temperature=35*u.K,
    exp_time=1*u.hour,
    n_frames=10,
)

#%%
# Put them all together
# ---------------------

config = PyConfig(
    target=target,
    geometry=geometry,
    atmosphere=atmosphere,
    generator=generator,
    telescope=telescope,
    noise=noise,
    gcm=gcm
    )
    

#%%
# Write the config to a file
# --------------------------
#
# This is optional. But it is nice if you want to use the GUI.

try:
    config.to_file(Path(__file__).parent / 'output' / 'psg_cfg.txt')
except NameError: # in case we are not in a notebook
    config.to_file(Path('output/psg_cfg.txt'))

#%%
# Run PSG
# -------

psg = APICall(
    cfg=config,
    output_type='rad',
    app='globes',
)
result = psg()

print(type(result))

#%%
# Plot the result
# ---------------

fig, ax = plt.subplots(1,1)

ax.plot(result.rad.wl,(result.rad['Proxima-Cen-b']/result.rad['Total']).to_value(u.dimensionless_unscaled)*1e6)
ax.set_xlabel(f'Wavelength ({result.rad.wl.unit})')
ax.set_ylabel(f'Flux (ppm)')

