"""
Configuration for pytest.
"""

from pypsg.docker import set_url_and_run

def pytest_sessionstart(session):
    """
    Set the psg URL and run the docker container if installed.
    """
    set_url_and_run()
