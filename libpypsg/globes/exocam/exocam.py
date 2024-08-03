"""
This module is designed to read output files from exoCAM.

This code is based on PSG conversion scripts for exoCAM
written by Geronimo Villanueva

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
from .. import waccm

TIME_UNIT = u.day
ALBEDO_DEFAULT = 0.3
EMISSIVITY_DEFAULT = 1.0
DEFAULT_DESCRIPTION = 'exoCAM Atmosphere Model'
TEST_URL = 'https://archive.org/download/SimulatedPhaseDependentSpectraOfTerrestrialAquaplanetsInMdwarfSystems/t3000_s1550_p7.74511.cam.h0.avg_n68.nc?#mode=bytes'
TEST_PATH = USER_DATA_PATH / 'data' / 'exocam_test.nc'

REQUIRED_VARIABLES = [
    "hyam",
    "hybm",
    "P0",
    "PS",
    "T",
    "lat",
    "lon",
    "PS",
    "time",
    "time_bnds"
]
OPTIONAL_VARIABLES = [
    "TS",
    "ASDIR",
    "U",
    "V",
]

MOLEC_TRANSLATOR = {
    # "PSG" : "WACCM",
    'CO2': 'co2vmr',
    'CH4': 'ch4vmr',
    'N2O': 'n2ovmr',
    'H2O': 'Q'
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
    'Water': 'CLDLIQ',
    'WaterIce': 'CLDICE',
}
AERO_FILL_VALUE = 1e-30
"""
Fill in nans and infs
"""
AERO_SIZE_TRANSLATOR = {
    # "PSG" : "WACCM",
    'Water_size': 'REL',
    'WaterIce_size': 'REI',
}
AERO_SIZE_FILL_VALUE = 1e-6
"""
Fill in nans and infs
"""

def validate_variables(data: Dataset):
    """
    Check to make sure that the file
    contains all necessary variables.

    Parameters
    ----------
    data : netCDF4.Dataset
        The data to be checked
    """
    missing_vars = []
    for var in REQUIRED_VARIABLES:
        try:
            data.variables[var]
        except KeyError:
            missing_vars.append(var)
    if len(missing_vars) == 0:
        pass
    else:
        raise KeyError(
            f'Dataset is missing required variables: {",".join(missing_vars)}'
        )

    missing_vars = []
    for var in OPTIONAL_VARIABLES:
        try:
            data.variables[var]
        except KeyError:
            missing_vars.append(var)
    if len(missing_vars) == 0:
        pass
    else:
        warnings.warn(
            f'Dataset is missing optional variables: {",".join(missing_vars)}',
            structure.VariableAssumptionWarning
        )


def get_time_index(data: Dataset, time: u.Quantity):
    """
    Get the index `itime` given a time quantity.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.
    time : astropy.units.Quantity
        The time Quantity.

    Returns
    -------
    itime : int
        The time index of `time`.
    """
    time_in_days = time.to_value(TIME_UNIT)
    time_left = data.variables['time_bnds'][:, 0]
    time_right = data.variables['time_bnds'][:, 1]
    itime = np.argwhere((time_in_days > time_left) &
                        (time_in_days <= time_right))[0][0]
    return itime


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
    n_time = data.variables['T'].shape[0]
    n_layers = data.variables['T'].shape[1]
    n_lat = data.variables['T'].shape[2]
    n_lon = data.variables['T'].shape[3]
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
    return waccm.waccm.get_psurf(data, itime)


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
    return waccm.waccm.get_pressure(data, itime)
    


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
    return waccm.waccm.get_temperature(data, itime)


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
    return waccm.waccm.get_tsurf(data, itime)
    


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
    return waccm.waccm.get_winds(data, itime)


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
    return waccm.waccm.get_albedo(data, itime)

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
    """
    return waccm.waccm.get_emissivity(data, itime)

def _generic_getter(data: Dataset, itime: int, name: str, translator: dict, fill_value: float, unit: u.Unit, cls: Type, mean_molec_mass:float=None):
    """
    Generic getter for a variable.
    """
    dat = waccm.waccm.generic_get_dat(data, itime, name, translator, fill_value, unit)
    if name == 'H2O':
        if mean_molec_mass is None:
            raise ValueError('Mean molecular mass must be specified for H2O.')
        dat = dat/ (1 - dat)
        dat = dat * (mean_molec_mass/18.0)
    dat = np.where(dat < 1e-30*unit, 1e-30*unit, dat)
    return cls(name, dat)


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
        The timestep to use.
    name : str
        The variable name of the aerosol.

    Returns
    -------
    aero : structure.Aerosol
        The concentration of the aerosol.
    """
    return _generic_getter(data, itime, f'{name}_size', AERO_SIZE_TRANSLATOR, AERO_SIZE_FILL_VALUE, psg_aerosol_size_unit, structure.AerosolSize)


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
    Covert a WACCM dataset to a Planet object.
    
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
        emissivity=get_emissivity(data,itime),
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