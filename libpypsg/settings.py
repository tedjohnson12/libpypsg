"""
PyPSG settings
==============

This module allows users to configure PyPSG.
"""
from pathlib import Path
from contextlib import contextmanager
import warnings
import json
from astropy import units as u

from . import __version__

REQUEST_TIMEOUT = 120

PSG_URL = 'https://psg.gsfc.nasa.gov/api.php'
PSG_PORT = 3000
INTERNAL_PSG_URL = f'http://localhost:{PSG_PORT}/api.php'

USER_DATA_PATH = Path.home() / '.libpypsg'
USER_SETTINGS_PATH = USER_DATA_PATH / 'settings.json'

DEFAULT_SETTINGS = {
    'url': PSG_URL,
    'api_key': None,
    'encoding': 'utf-8',
    'cfg_max_lines': 1500,
    'timeout': REQUEST_TIMEOUT,
    'header': {'User-Agent': f'libpypsg/{__version__}'},
}

TEMPORARY_SETTINGS = {}


settings_need_reload = False
def save_settings(**kwargs):
    """
    Save new user settings to file.
    
    This file is usually located at `~/.libpypsg/settings.json`.
    
    Parameters
    ----------
    kwargs : dict
        The settings to save.
    """
    if not USER_DATA_PATH.exists():
        USER_DATA_PATH.mkdir()
    if not USER_SETTINGS_PATH.exists():
        USER_SETTINGS_PATH.touch()
    with USER_SETTINGS_PATH.open('r') as file:
        try:
            previous_settings = json.load(file)
        except json.decoder.JSONDecodeError:
            previous_settings = {}
        
    for key, value in kwargs.items():
        if key in DEFAULT_SETTINGS.keys():
            previous_settings[key] = value
        else:
            raise KeyError(f'Unknown setting {key}.')
    with USER_SETTINGS_PATH.open('w') as file:
        json.dump(previous_settings, file, indent=4)
    # pylint: disable-next=global-statement
    global settings_need_reload
    settings_need_reload = True
    reload_settings()

def load_settings():
    """
    Get user settings from file or use defaults.
    
    Returns
    -------
    settings : dict
        The user settings.
    """
    try:
        with USER_SETTINGS_PATH.open('r') as file:
            try:
                settings = json.load(file)
            except json.decoder.JSONDecodeError:
                settings = {}
    except FileNotFoundError:
        settings = {}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
    return settings

user_settings = load_settings()

def reload_settings():
    """
    Refreshes the settings stored in memory.
    """
    # pylint: disable-next=global-statement
    global user_settings
    user_settings = load_settings()
    # pylint: disable-next=global-statement
    global settings_need_reload
    settings_need_reload = False

class StaleSettingsWarning(RuntimeWarning):
    """
    Warning raised when the user settings have changed but have not been reloaded.
    """
    pass


@contextmanager
def temporary_settings(**kwargs):
    """
    Create a temporary settings context.
    
    Parameters
    ----------
    kwargs : dict
        The settings to set.
    
    Examples
    --------
    >>> with temporary_settings(url='https://psg.gsfc.nasa.gov/api.php'):
    ...     print(get_setting('url'))
    https://psg.gsfc.nasa.gov/api.php
    """
    for key in kwargs:
        if key not in DEFAULT_SETTINGS.keys():
            raise KeyError(f'Unknown setting {key}.')
    global TEMPORARY_SETTINGS
    TEMPORARY_SETTINGS = kwargs
    try:
        yield
    finally:
        TEMPORARY_SETTINGS = {}


def get_setting(key):
    """
    Get a setting.
    
    This function checks for context first, then the saved settings, and finally the defaults.
    
    Parameters
    ----------
    key : str
        The setting to get.
    
    Returns
    -------
    value : any
        The value of the setting.
    
    Raises
    ------
    KeyError
        If the setting is not found.
    """
    if settings_need_reload:
        msg = 'Your user settings have changed recently.\n'
        msg += 'Please reload the settings using the `libpypsg.settings.reload_settings()` function.'
        warnings.warn(msg,StaleSettingsWarning) 
    if key in TEMPORARY_SETTINGS:
        return TEMPORARY_SETTINGS[key]
    if key in user_settings:
        return user_settings[key]
    else:
        raise KeyError(f'Unknown setting {key}.')
    



################################
# Some settings related to PSG #
################################

psg_pressure_unit = u.bar
"""
PSG atmospheric pressure unit.

This unit is determined by PSG and used to standardize
the atmospheric pressure of planets in VSPEC.

:type: astropy.units.Unit
"""
psg_aerosol_size_unit = u.m
"""
PSG aerosol size unit.

This unit is determined by PSG and used to
standardize aerosol size in VSPEC.

:type: astropy.units.Unit
"""

atmosphere_type_dict = {'H2':45,'He':0,'H2O':1,'CO2':2,'O3':3,'N2O':4,'CO':5,'CH4':6,'O2':7,
                        'NO':8,'SO2':9,'NO2':10,'N2':22,'HNO3':12,'HO2NO2':'SEC[26404-66-0] Peroxynitric acid',
                        'N2O5':'XSEC[10102-03-1] Dinitrogen pentoxide','O':'KZ[08] Oxygen',
                        'OH':'EXO[OH]'}
"""
A dictionary mapping molecular species to the default
database to use to create opacities. These are all
internal to PSG, but must be set by ``VSPEC``.

Integers mean that we want to use data from the HITRAN database, which for a number ``N``
is represented in PSG by ``HIT[N]``. Strings are sent straight to PSG as is.

:type: dict
"""

aerosol_name_dict = {
    'Water':{
        'name':'CLDLIQ',
        'size':'REL'
    },
    'WaterIce':{
        'name':'CLDICE',
        'size':'REI'
    }
}
"""
A dictionary mapping aerosol species from their PSG name
to their name in the WACCM NetCDF format.

:type: dict
"""

aerosol_type_dict = {
    'Water': 'AFCRL_Water_HRI',
    'WaterIce': 'Warren_ice_HRI'
}
"""
A dictionary mapping aerosol species to the default
database to use. These are all
internal to PSG, but must be set by ``VSPEC``.

:type: dict
"""