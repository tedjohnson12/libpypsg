"""
Test pypsg.request module.
"""
import pytest
from astropy import units as u

from pypsg import PyConfig, APICall, PyRad, PyLyr
from pypsg import request as psgrequest


@pytest.fixture
def default_cfg():
    """
    Get a simple default configuration object.
    """
    return PyConfig.from_dict({'OBJECT-NAME': 'Test'})

def test_api_init(default_cfg):
    """
    Test api intialization.
    """
    api = APICall(default_cfg, 'rad', 'globes', 'testurl')
    assert api.url == 'testurl'
    assert api.app == 'globes'
    assert api._type == 'rad'
    assert api.cfg.target.name.value == 'Test'

def test_api_call_rad(default_cfg):
    """
    Test api call.
    """
    api = APICall(default_cfg, 'rad')
    response = api()
    assert isinstance(response,psgrequest.PSGResponse)
    assert isinstance(response.rad, PyRad)
    assert isinstance(response.rad.wl, u.Quantity)

def test_api_call_all(default_cfg):
    """
    Test api call.
    """
    api = APICall(default_cfg, 'all')
    response = api()
    assert isinstance(response,psgrequest.PSGResponse)
    assert isinstance(response.cfg, PyConfig)
    assert isinstance(response.rad, PyRad)

def test_api_call_multiple(default_cfg):
    """
    Test api call.
    """
    with pytest.raises(NotImplementedError):
        _ = APICall(default_cfg, ('rad', 'cfg'))
        
        
if __name__ == '__main__':
    pytest.main(args=[__file__])
