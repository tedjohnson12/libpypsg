"""
Test the `pypsg.docker` module.
"""

import time
import pytest

from pypsg import docker as psgdocker


@pytest.mark.local
def test_is_psg_installed(psg_url):
    """
    Test the `is_psg_installed` function.
    """
    assert psgdocker.is_psg_installed()


@pytest.mark.local
def test_is_psg_running(psg_url):
    """
    Test the `is_psg_running` function.
    """
    assert psgdocker.is_psg_running()


@pytest.mark.local
def test_psg_start_stop(psg_url):
    """
    Test the `start_psg` function.
    """
    started_out_running = psgdocker.is_psg_running()
    psgdocker.start_psg()
    assert psgdocker.is_psg_running()
    psgdocker.stop_psg()
    assert not psgdocker.is_psg_running()
    psgdocker.start_psg()
    assert psgdocker.is_psg_running()
    if not started_out_running:
        psgdocker.stop_psg()
    assert started_out_running == psgdocker.is_psg_running()
    # give the container time to setup. This is important for other tests
    time.sleep(1)

if __name__ in '__main__':
    pytest.main(args=[__file__])