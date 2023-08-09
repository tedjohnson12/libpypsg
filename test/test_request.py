
from pypsg.request import apiCall
from pypsg.cfg.cfg import Config,StringParam


def test_api_init():
    config = Config(StringParam('object-name','Exoplanet'))
    psg = apiCall(
        cfg=config,
        output_type='cfg',
        app=None,
        url='https://psg.gsfc.nasa.gov/api.php'
    )
    assert isinstance(psg.cfg,Config)
    assert psg.type == 'cfg'
    assert psg.app == None
    assert psg.url == 'https://psg.gsfc.nasa.gov/api.php'

def test_api_call():
    config = Config(StringParam('object-name','Exoplanet'))
    psg = apiCall(
        cfg=config,
        output_type='cfg',
        app=None,
        url='https://psg.gsfc.nasa.gov/api.php'
    )
    content = psg()
    assert b'<OBJECT-NAME>Exoplanet' in content