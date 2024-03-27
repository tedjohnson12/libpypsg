"""
Convert `exoplasim` outputs to the `pypsg` format.
"""

import warnings
import requests
from typing import Tuple, Type
from netCDF4 import Dataset
from astropy import units as u
import numpy as np

from ...settings import psg_aerosol_size_unit, USER_DATA_PATH
from .. import structure
from ..globes import PyGCM
from ..exocam.exocam import _generic_getter


DEFAULT_DESCRIPTION = 'exoplasim model'
TEST_URL = 'https://borealisdata.ca/api/access/datafile/712946'
TEST_PATH = USER_DATA_PATH / 'data' / 'exoplasim_test.nc'

ALBEDO_DEFAULT = 0.3
MOLEC_TRANSLATOR = {
    # "PSG" : "WACCM",
    'H2O': 'hus',
}
"""
Translate molecule names to WACCM
"""
MOLEC_FILL_VALUE = 1e-30
"""
Fill in nans and infs
"""

AERO_TRANSLATOR = {
    # "PSG" : "WACCM",
    'Water': 'clw',
}
AERO_FILL_VALUE = 1e-30
"""
Fill in nans and infs
"""
AERO_SIZE_TRANSLATOR = {
    # "PSG" : "WACCM",
}
AERO_SIZE_FILL_VALUE = 1e-6
"""
Fill in nans and infs
"""


def get_shape(data: Dataset):
    """
    Get the shape of a Dataset

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.

    Returns
    -------
    tuple
        The shape of `data`, (N_time,N_layers,N_lat,N_lon)
    """
    n_time = data.variables['time'].shape[0]
    n_layers = data.variables['lev'].shape[0]
    n_lat = data.variables['lat'].shape[0]
    n_lon = data.variables['lon'].shape[0]
    return n_time, n_layers, n_lat, n_lon

def get_psurf(data: Dataset, itime: int) -> structure.SurfacePressure:
    """
    Get the surface pressure.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    psurf : structure.SurfacePressure
        The surface pressure
    """
    psurf = data.variables['ps'][itime, :, :].T
    ps_unit = u.Unit(data.variables['ps'].units)
    return structure.SurfacePressure(psurf * ps_unit)

def get_pressure(data: Dataset, itime: int) -> structure.Pressure:
    """
    Get the pressure.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    pressure : structure.Pressure
        The pressure.
    """
    press = data.variables['flpr'][itime, :, :, :]
    press = np.swapaxes(press, 1, 2)
    press = np.flip(press, axis=0)
    unit = u.Unit(data.variables['flpr'].units)
    
    return structure.Pressure(press*unit) 

def get_temperature(data: Dataset, itime: int) -> structure.Temperature:
    """
    Get the temperature.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    temperature : structure.Temperature
        The temperature.
    """
    temperature = np.flip(
        np.array(data.variables['ta'][itime, :, :, :]), axis=0)
    temperature = u.Unit(data.variables['ta'].units) * temperature
    temperature = np.swapaxes(temperature, 1,2)
    return structure.Temperature(temperature)

def get_tsurf(data: Dataset, itime: int) -> structure.SurfaceTemperature:
    """
    Get the surface temperature.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    tsurf : structure.SurfaceTemperature
        The surface temperature.
    """
    try:
        tsurf = np.array(data.variables['ts'][itime, :, :]).T
        tsurf = u.Unit(data.variables['ts'].units) * tsurf
    except KeyError:
        msg = 'Surface Temperature not explicitly stated. '
        msg += 'Using the value from the lowest layer.'
        warnings.warn(msg, structure.VariableAssumptionWarning)
        temp = get_temperature(data, itime).dat
        tsurf = temp[0, :, :]
    return structure.SurfaceTemperature(tsurf[:, :])

def get_winds(data: Dataset, itime: int) -> Tuple[structure.Wind, structure.Wind]:
    """
    Get the winds.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    U : structure.Wind
        The wind speed in the U direction.
    V : structure.Wind
        The wind speed in the V direction.
    """
    try:
        wind_u = np.flip(np.array(data.variables['ua'][itime, :, :, :]), axis=0)
        wind_u = u.Unit(data.variables['ua'].units) * wind_u
    except KeyError:
        msg = 'Wind Speed U not explicitly stated. Assuming zero.'
        warnings.warn(msg, structure.VariableAssumptionWarning)
        _, nlayers, nlat, nlon = get_shape(data)
        wind_u = np.zeros((nlayers, nlat, nlon)) * u.m / u.s
    try:
        wind_v = np.flip(np.array(data.variables['va'][itime, :, :, :]), axis=0)
        wind_v = u.Unit(data.variables['va'].units) * wind_v
    except KeyError:
        msg = 'Wind Speed V not explicitly stated. Assuming zero.'
        warnings.warn(msg, structure.VariableAssumptionWarning)
        _, nlayers, nlat, nlon = get_shape(data)
        wind_v = np.zeros((nlayers, nlat, nlon)) * u.m / u.s
    wind_u = np.swapaxes(wind_u, 1, 2)
    wind_v = np.swapaxes(wind_v, 1, 2)
    return structure.Wind('wind_u', wind_u), structure.Wind('wind_v', wind_v)

def get_albedo(data: Dataset, itime: int) -> structure.Albedo:
    """
    Get the albedo.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    albedo : structure.Albedo
        The albedo.
    """
    try:
        albedo = np.array(data.variables['alb'][itime, :, :])
        albedo = np.where((albedo >= 0) & (albedo <= 1.0) & (
            np.isfinite(albedo)), albedo, ALBEDO_DEFAULT)
    except KeyError:
        msg = f'Albedo not explicitly stated. Using {ALBEDO_DEFAULT}.'
        warnings.warn(msg, structure.VariableAssumptionWarning)
        _, _, nlat, nlon = get_shape(data)
        albedo = np.ones((nlat, nlon)) * ALBEDO_DEFAULT
    return structure.Albedo(albedo.T*u.dimensionless_unscaled)

def get_emissivity(data: Dataset, itime: int) -> structure.Emissivity:
    """
    Get the emissivity.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.

    Returns
    -------
    emissivity : structure.Emissivity
        The Emissivity.
    
    Notes
    -----
    As far as I can tell there is no emissivity variable in the test dataset.
    """
    raise NotImplementedError('I don\'t know if exoplasim supports emissivity.')

def get_molecule(data: Dataset, itime: int, name: str, mean_molecular_mass: float=None) -> structure.Molecule:
    """
    Get the abundance of a molecule.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.
    name : str
        The variable name of the molecule.
    mean_molecular_mass : float, optional
        The mean molecular mass of the atmosphere. This is required to extract
        the water abundance from the specific humidity variable.

    Returns
    -------
    molec : structure.Molecule
        The concentration of the molecule.
    """
    return _generic_getter(data, itime, name, MOLEC_TRANSLATOR, MOLEC_FILL_VALUE, u.dimensionless_unscaled, structure.Molecule, mean_molecular_mass)

def get_aerosol(data: Dataset, itime: int, name: str) -> structure.Aerosol:
    """
    Get the abundance of an aerosol.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.
    name : str
        The variable name of the aerosol.

    Returns
    -------
    aero : structure.Aerosol
        The concentration of the aerosol.
    """
    return _generic_getter(data, itime, name, AERO_TRANSLATOR, MOLEC_FILL_VALUE, u.dimensionless_unscaled, structure.Aerosol)

def get_aerosol_size(data: Dataset, itime: int, name: str) -> structure.AerosolSize:
    """
    Get the size of an aerosol.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use. This is included for consistency with other modules.
    name : str
        The variable name of the aerosol.

    Returns
    -------
    aero : structure.Aerosol
        The concentration of the aerosol.
    """
    _ = itime
    _, n_layer, n_lat, n_lon = get_shape(data)
    return structure.AerosolSize(
        f'{name}_size',
        AERO_SIZE_FILL_VALUE * np.ones((n_layer,n_lon,n_lat)) * psg_aerosol_size_unit
    )

def get_molecule_suite(data: Dataset, itime: int, names: list, background: str = None, mean_molecular_mass: float=None) -> Tuple[structure.Molecule]:
    """
    Get the abundance of a suite of molecules.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    itime : int
        The timestep to use.
    names : list of str
        The variable names of the molecules.
    background : str, default=None
        The variable name of a background gas to include.

    Returns
    -------
    molec : tuple of structure.Molecule
        The molecules in the GCM
    """
    molecs = tuple(get_molecule(data, itime, name, mean_molecular_mass) for name in names)
    if background is not None:
        if background in names:
            raise ValueError(
                'Do not know how to handle specifying a background'
                'gas that is already in our dataset.'
            )
        else:
            _, n_layer, n_lat, n_lon = get_shape(data)
            background_abn = np.ones(
                shape=(n_layer, n_lon, n_lat))*u.dimensionless_unscaled
            for molec in molecs:
                background_abn -= molec.dat
            if np.any(background_abn < 0):
                raise ValueError('Cannot have negative abundance.')
            molecs += (structure.Molecule(background, background_abn),)
    return molecs

def to_pygcm(
    data:Dataset,
    itime:int,
    molecules:list,
    aerosols:list,
    background=None,
    lon_start:float=-180.,
    lat_start:float=-90.,
    desc:str=DEFAULT_DESCRIPTION,
    mean_molecular_mass:float=None
)->PyGCM:
    """
    Covert an exoplasim dataset to a Planet object.
    
    Parameters
    ----------
    data : netCDF4.Dataset
        The GCM dataset.
    itime : int
        The time index.
    molecules : list
        The variable names of the molecules.
    aerosols : list
        The variable names of the aerosols.
    background : str, optional
        The optional background gas to assume.
    lon_start : float, optional
        The starting longitude of the GCM. Defaults to -180.
    lat_start : float, optional
        The starting latitude of the GCM. Defaults to -90.
    desc : str, optional
        The description of the GCM.'
    mean_molecular_mass : float, optional
        The mean molecular mass of the atmosphere. Defaults to None.
    """
    molecules:tuple = tuple() if molecules is None else get_molecule_suite(data,itime,molecules,background,mean_molecular_mass)
    
    _aerosols:tuple = tuple() if aerosols is None else tuple(get_aerosol(data,itime,name) for name in aerosols)
    aerosol_sizes:tuple = tuple() if aerosols is None else tuple(get_aerosol_size(data,itime,name) for name in aerosols)
    
    wind_u, wind_v = get_winds(data,itime)
    
    return PyGCM(
        get_pressure(data,itime),
        get_temperature(data,itime),
        *(molecules + _aerosols + aerosol_sizes),
        wind_u=wind_u,
        wind_v=wind_v,
        tsurf=get_tsurf(data,itime),
        psurf=get_psurf(data,itime),
        albedo=get_albedo(data,itime),
        emissivity=None,
        lon_start=lon_start,
        lat_start=lat_start,
        desc=desc
    )

def download_test_data(rewrite=False):
    """
    Download the WACCM test data.
    """
    TEST_PATH.parent.mkdir(exist_ok=True)
    if TEST_PATH.exists() and not rewrite:
        return TEST_PATH
    else:
        TEST_PATH.unlink(missing_ok=True)
        with requests.get(TEST_URL,stream=True,timeout=20) as req:
            req.raise_for_status()
            with TEST_PATH.open('wb') as f:
                for chunk in req.iter_content(chunk_size=8192):
                    f.write(chunk)
        return TEST_PATH