"""
Test pypsg.request module.
"""
from pathlib import Path
import pytest
from astropy import units as u

from pypsg import PyConfig, APICall, PyRad, PyLyr
from pypsg import request as psgrequest


@pytest.fixture
def default_cfg():
    """
    Get a simple default configuration object.
    """
    return PyConfig.from_file(Path(__file__).parent / 'data' / 'simple.cfg')


@pytest.fixture
def advanced_cfg():
    """
    A more complex configuration object. 
    """
    return PyConfig.from_file(Path(__file__).parent / 'data' / 'advanced.cfg')
# pylint: disable=redefined-outer-name


def test_api_init(default_cfg):
    """
    Test api intialization.
    """
    api = APICall(default_cfg, 'rad', 'globes', 'testurl')
    assert api.url == 'testurl'
    assert api.app == 'globes'
    assert api.type == 'rad'
    assert api.cfg.target.object.value == 'Exoplanet'


def test_api_call_rad(default_cfg,psg_url):
    """
    Test api call.
    """
    api = APICall(default_cfg, 'rad',url=psg_url)
    response = api()
    assert isinstance(response, psgrequest.PSGResponse)
    assert isinstance(response.rad, PyRad)
    assert isinstance(response.rad.wl, u.Quantity)


def test_api_call_all(default_cfg, psg_url):
    """
    Test api call.
    """
    api = APICall(default_cfg, 'all',url=psg_url)
    response = api()
    assert isinstance(response, psgrequest.PSGResponse)
    assert isinstance(response.cfg, PyConfig)
    assert isinstance(response.rad, PyRad)


def test_api_call_multiple(default_cfg):
    """
    Test api call.
    """
    with pytest.raises(NotImplementedError):
        _ = APICall(default_cfg, ('rad', 'cfg'))


def test_api_call_advanced(advanced_cfg, psg_url):
    """
    Test api call.
    """
    api = APICall(advanced_cfg, 'all',url=psg_url)
    response = api()
    assert isinstance(response, psgrequest.PSGResponse)
    assert isinstance(response.rad, PyRad)
    assert isinstance(response.lyr, PyLyr)
    assert isinstance(response.noi, PyRad)
    assert isinstance(response.cfg, PyConfig)
    assert response.rad.wl.unit == u.micron


if __name__ == '__main__':
    pytest.main(args=[__file__])
