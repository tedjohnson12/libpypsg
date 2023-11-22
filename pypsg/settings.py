"""
Global settings
"""
from pathlib import Path
import warnings
import json

REQUEST_TIMEOUT = 120

PSG_URL = 'https://psg.gsfc.nasa.gov/api.php'
INTERNAL_PSG_URL = 'https://localhost:3000/api.php'

USER_DATA_PATH = Path.home() / '.pypsg'
USER_SETTINGS_PATH = USER_DATA_PATH / 'settings.json'

DEFAULT_SETTINGS = {
    'url': PSG_URL,
    'api_key': None
}


settings_need_reload = False
def save_settings(**kwargs):
    if not USER_DATA_PATH.exists():
        USER_DATA_PATH.mkdir()
    with USER_SETTINGS_PATH.open('r') as file:
        previous_settings = json.load(file)
        
    for key, value in kwargs.items():
        if key in DEFAULT_SETTINGS.keys():
            previous_settings[key] = value
        else:
            raise KeyError(f'Unknown setting {key}.')
    with USER_SETTINGS_PATH.open('w') as file:
        json.dump(previous_settings, file, indent=4)
    print(f'Saved settings to {USER_SETTINGS_PATH}')
    # pylint: disable-next=global-statement
    global settings_need_reload
    settings_need_reload = True
    print('Reloading settings...')
    reload_settings()

def load_settings():
    with USER_SETTINGS_PATH.open('r') as file:
        settings = json.load(file)
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
    # pylint: disable-next=global-statement
    global settings_need_reload
    settings_need_reload = False
    return settings

user_settings = load_settings()

def reload_settings():
    # pylint: disable-next=global-statement
    global user_settings
    user_settings = load_settings()

class StaleSettingsWarning(RuntimeWarning):
    pass

def get_setting(key):
    if settings_need_reload:
        msg = 'Your user settings have changed recently.\n'
        msg += 'Please reload the settings using the `pypsg.settings.reload_settings()` function.'
        warnings.warn(msg,StaleSettingsWarning) 
    if key in user_settings:
        return user_settings[key]
    else:
        raise KeyError(f'Unknown setting {key}.')