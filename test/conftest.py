"""
Configuration for pytest.
"""
import pytest
import time

from pypsg.docker import set_url_and_run, stop_psg
from pypsg import settings

def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add options to pytest.
    """
    parser.addoption('--local', action='store_true', help='Expect a local psg installation')
    parser.addoption('--slow', action='store_true', help='run slow tests')

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    should_skip_local = not config.getoption("--local")
    should_skip_slow = not config.getoption("--slow")
    skip_local = pytest.mark.skip(reason="need --local option to run")
    skip_slow = pytest.mark.skip(reason="need --slow option to run")
    for item in items:
        if "local" in item.keywords and should_skip_local:
            item.add_marker(skip_local)
        if "slow" in item.keywords and should_skip_slow:
            item.add_marker(skip_slow)


@pytest.fixture
def psg_url(request: pytest.FixtureRequest)->str:
    """
    Decide which psg URL to use.
    """
    local = request.config.getoption('--local')
    if not local:
        yield settings.PSG_URL
    else:
        set_url_and_run()
        time.sleep(1) # give the container time to start
        yield settings.INTERNAL_PSG_URL
        stop_psg(strict=False)

