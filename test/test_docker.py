"""
Test the `pypsg.docker` module.
"""
import pytest

from pypsg import docker as psgdocker

@pytest.mark.skip(reason='Depends on the test environment')
def test_is_psg_installed():
    """
    Test the `is_psg_installed` function.
    """
    assert psgdocker.is_psg_installed()

@pytest.mark.skip(reason='Depends on the test environment')
def test_is_psg_running():
    """
    Test the `is_psg_running` function.
    """
    assert psgdocker.is_psg_running()

@pytest.mark.skipif(not psgdocker.is_psg_installed(), reason='Depends on the test environment')
def test_psg_start_stop():
    """
    Test the `start_psg` function.
    """
    init_state = psgdocker.is_psg_running()
    psgdocker.start_psg()
    assert psgdocker.is_psg_running()
    psgdocker.stop_psg()
    assert not psgdocker.is_psg_running()
    psgdocker.start_psg()
    assert psgdocker.is_psg_running()
    if not init_state:
        psgdocker.stop_psg()
        
    