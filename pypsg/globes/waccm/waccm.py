"""
This module is designed to read output files from the
Whole Atmosphere Community Climate Model (WACCM) code
and convert it from netCDF to PSG file types.

The WACCM models used in writing this were produced by 
Howard Chen in 2023

This code is based on PSG conversion scripts for exoCAM
written by Geronimo Villanueva

"""
import warnings
from typing import Tuple, Type
from netCDF4 import Dataset
from astropy import units as u
import numpy as np

from ...settings import psg_aerosol_size_unit
from .. import structure
from ..globes import PyGCM

TIME_UNIT = u.day
ALBEDO_DEFAULT = 0.3
EMISSIVITY_DEFAULT = 1.0
DEFAULT_DESCRIPTION = 'Whole Atmosphere Community Climate Model (WACCM)'

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
    'NO2': 'NOX'
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
    'Water': 'REL',
    'WaterIce': 'REI',
}
AERO_SIZE_FILL_VALUE = 1e-6
"""
Fill in nans and infs
"""


class VariableAssumptionWarning(UserWarning):
    """
    A warning raised when a variable
    is not found in the netCDF file.
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
            VariableAssumptionWarning
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
    psurf = data.variables['PS'][itime, :, :]
    ps_unit = u.Unit(data.variables['PS'].units)
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
    hyam = np.flipud(data.variables['hyam'][:])
    hybm = np.flipud(data.variables['hybm'][:])
    ps = get_psurf(data, itime)
    pressure = hyam[:, np.newaxis, np.newaxis] + \
        hybm[:, np.newaxis, np.newaxis] * ps.dat[np.newaxis, :, :]
    return structure.Pressure(pressure)


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
        np.array(data.variables['T'][itime, :, :, :]), axis=0)
    temperature = u.Unit(data.variables['T'].units) * temperature
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
        tsurf = np.array(data.variables['TS'][itime, :, :])
        tsurf = u.Unit(data.variables['TS'].unit) * tsurf
    except KeyError:
        msg = 'Surface Temperature not explicitly stated. '
        msg += 'Using the value from the lowest layer.'
        warnings.warn(msg, VariableAssumptionWarning)
        temp = get_temperature(data, itime).dat
        tsurf = temp[0, :, :] * u.Unit(data.variables['T'].unit)
    return structure.SurfaceTemperature(temp[0, :, :])


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
        wind_u = np.flip(np.array(data.variables['U'][itime, :, :, :]), axis=0)
        wind_u = u.Unit(data.variables['U'].unit) * wind_u
    except KeyError:
        msg = 'Wind Speed U not explicitly stated. Assuming zero.'
        warnings.warn(msg, VariableAssumptionWarning)
        _, nlayers, nlat, nlon = get_shape(data)
        wind_u = np.zeros((nlayers, nlat, nlon)) * u.m / u.s
    try:
        wind_v = np.flip(np.array(data.variables['V'][itime, :, :, :]), axis=0)
        wind_v = u.Unit(data.variables['V'].unit) * wind_v
    except KeyError:
        msg = 'Wind Speed V not explicitly stated. Assuming zero.'
        warnings.warn(msg, VariableAssumptionWarning)
        _, nlayers, nlat, nlon = get_shape(data)
        wind_v = np.zeros((nlayers, nlat, nlon)) * u.m / u.s
    return structure.Wind('wind_u', wind_u), structure.Wind('wind_v', wind_v)


def get_coords(data: Dataset):
    """
    Get latitude and longitude coordinates.

    Parameters
    ----------
    data : netCDF4.Dataset
        The dataset to use.

    Returns
    -------
    lat : np.ndarray
        The latitude coordinates in degrees (N_lat,)
    lon : np.ndarray
        The longitude coodinates in degrees (N_lon,)
    """
    lat = np.array(data.variables['lat'][:])
    lon = np.array(data.variables['lon'][:])
    return lat, lon


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
        albedo = np.array(data.variables['ASDIR'][itime, :, :])
        albedo = np.where((albedo >= 0) & (albedo <= 1.0) & (
            np.isfinite(albedo)), albedo, ALBEDO_DEFAULT)
    except KeyError:
        msg = f'Albedo not explicitly stated. Using {ALBEDO_DEFAULT}.'
        warnings.warn(msg, VariableAssumptionWarning)
        _, _, nlat, nlon = get_shape(data)
        albedo = np.ones((nlat, nlon)) * ALBEDO_DEFAULT
    return structure.Albedo(albedo)

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
    try:
        emissivity = np.array(data.variables['EMISS'][itime, :, :])
        emissivity = np.where((emissivity >= 0) & (emissivity <= 1.0) & (
            np.isfinite(emissivity)), emissivity, EMISSIVITY_DEFAULT)
    except KeyError:
        msg = f'Emissivity not explicitly stated. Using {EMISSIVITY_DEFAULT}.'
        warnings.warn(msg, VariableAssumptionWarning)
        _, _, nlat, nlon = get_shape(data)
        emissivity = np.ones((nlat, nlon)) * EMISSIVITY_DEFAULT
    return structure.Emissivity(emissivity)


def _generic_getter(data: Dataset, itime: int, name: str, translator: dict, fill_value: float, unit: u.Unit, cls: Type):
    """
    Generic getter for a variable.
    """
    dat = np.flip(
        np.array(data.variables[translator.get(name, name)][itime, :, :, :]), axis=0)
    dat = np.where((dat > 0) & (np.isfinite(dat)), dat, fill_value) * unit
    return cls(name, dat)


def get_molecule(data: Dataset, itime: int, name: str) -> structure.Molecule:
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

    Returns
    -------
    molec : structure.Molecule
        The concentration of the molecule.
    """
    return _generic_getter(data, itime, name, MOLEC_TRANSLATOR, MOLEC_FILL_VALUE, u.dimensionless_unscaled, structure.Molecule)


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
    return _generic_getter(data, itime, name, AERO_SIZE_TRANSLATOR, AERO_SIZE_FILL_VALUE, psg_aerosol_size_unit, structure.AerosolSize)


def get_molecule_suite(data: Dataset, itime: int, names: list, background: str = None) -> Tuple[structure.Molecule]:
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
    molecs = (get_molecule(data, itime, name) for name in names)
    if background is not None:
        if background in names:
            raise ValueError(
                'Do not know how to handle specifying a background'
                'gas that is already in our dataset.'
            )
        else:
            _, n_layer, n_lat, n_lon = get_shape(data)
            background_abn = np.ones(
                shape=(n_layer, n_lat, n_lon))*u.dimensionless_unscaled
            for molec in molecs:
                background_abn -= molec.dat
            if np.any(background_abn < 0):
                raise ValueError('Cannot have negative abundance.')
            molecs += tuple(structure.Molecule(background, background_abn))
    return molecs

def to_pygcm(
    data:Dataset,
    itime:int,
    molecules:list,
    aerosols:list,
    background=None,
    lon_start:float=-180.,
    lon_end:float=-90.,
    desc:str=DEFAULT_DESCRIPTION
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
    """
    molecules:tuple = get_molecule_suite(data,itime,molecules,background)
    
    aerosols:tuple = (get_aerosol(data,itime,name) for name in aerosols)
    aerosol_sizes:tuple = (get_aerosol_size(data,itime,name) for name in aerosols)
    
    wind_u, wind_v = get_winds(data,itime)
    
    return PyGCM(
        pressure=get_pressure(data,itime),
        *molecules,
        *aerosols,
        *aerosol_sizes,
        wind_u=wind_u,
        wind_v=wind_v,
        temperature=get_temperature(data,itime),
        tsurf=get_tsurf(data,itime),
        psurf=get_psurf(data,itime),
        albedo=get_albedo(data,itime),
        emissivity=get_emissivity(data,itime),
        lon_start=lon_start,
        lon_end=lon_end,
        description=desc
    )
