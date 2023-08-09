"""
Global settings
"""
from pathlib import Path

REQUEST_TIMEOUT = 120

PSG_URL = 'https://psg.gsfc.nasa.gov/api.php'
INTERNAL_PSG_URL = 'https://localhost:3000/api.php'

USER_DATA_PATH = Path.home() / '.pypsg'

API_KEY_PATH = USER_DATA_PATH / 'api_key.txt'