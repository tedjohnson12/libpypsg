"""
Test the user interface
"""
import pytest
import requests
from pathlib import Path

from pypsg.cfg import PyConfig, BinConfig
from pypsg import settings
from pypsg.exceptions import GlobESError, PSGMultiError
from pypsg.settings import INTERNAL_PSG_URL, PSG_URL
from pypsg.docker import start_psg, stop_psg, is_psg_installed
from pypsg import APICall, PSGResponse, PyRad, PyLyr

TR1e_PATH = Path(__file__).parent / 'test_cfg' / 'data' / 'TR1e_mirecle.cfg'

@pytest.fixture
def keep_psg_settings():
    orginal_url = settings.get_setting('url')
    yield None
    settings.save_settings(url=orginal_url)


def test_apicall(keep_psg_settings):
    """
    Test user interaction with the APICall class
    
    Parameters
    ----------
    cfg : Config or BinConfig
        A configuration object. We won't worry about its contents for this test, but it can be a `BinConfig` or a `PyConfig`.
    output_type : str or None
        The type of output to ask for. This could be a specific file type, set, update, all, or None
    app : str or None
        The app to use. Either None of 'globes'
    url : str or None
        The URL to send the request to. This can be the external URL or the internal URL. It also can be None.
    
    Public Attributes
    -----------------
    None
    
    Public Methods
    --------------
    __call__(self)
        Calls the PSG API and returns a `PSGResponse` object.
    
    Other Expectations
    ------------------
    * If PSG is not running and the internal URL is specified, an exception will be raised.
    * If globes is used but there is not GCM an exception will be raised.
        - This seems to not be the case when output is `all` and the docker version is used.
    
    """
    
    cfgs = [PyConfig.from_file(TR1e_PATH), BinConfig.from_file(TR1e_PATH)]
    output_types = [None,'all','cfg', 'rad', 'lyr', 'noi', 'upd', 'set']
    apps = ['globes', None]
    urls = [None, INTERNAL_PSG_URL, PSG_URL] if is_psg_installed() else [None, PSG_URL]
    url_settings = [INTERNAL_PSG_URL, PSG_URL] if is_psg_installed() else [PSG_URL]
    is_psg_running = [False, True] if is_psg_installed() else [False]    
    
    def check(
        psg_running,
        cfg,
        output_type,
        app,
        url,
        url_setting
    ):
        api = APICall(
            cfg=cfg,
            output_type=output_type,
            app=app,
            url=url
            )
        resolved_url = url if url is not None else url_setting
        expect_globes_err = app == 'globes'
        expect_globes_err = expect_globes_err and output_type not in ['set','upd']
        
        if not psg_running and resolved_url == INTERNAL_PSG_URL:
            with pytest.raises(requests.ConnectionError):
                _ = api()
        elif expect_globes_err:
            with pytest.raises((GlobESError,PSGMultiError)):
                _ = api()
            APICall(cfg=cfg, output_type='set', app=None, url=url)() # This should clean up
        else:
            response = api()
            assert isinstance(response, PSGResponse)
            match output_type:
                case 'cfg':
                    assert isinstance(response.cfg, PyConfig)
                    assert response.rad is None
                    assert response.lyr is None
                    assert response.noi is None
                    assert response.cfg.target.object.value == 'Exoplanet'
                case 'rad':
                    assert isinstance(response.rad, PyRad)
                    assert response.cfg is None
                    assert response.lyr is None
                    assert response.noi is None
                case 'lyr':
                    assert isinstance(response.lyr, PyLyr)
                    assert response.cfg is None
                    assert response.rad is None
                    assert response.noi is None
                case 'noi':
                    assert isinstance(response.noi, PyRad)
                    assert response.cfg is None
                    assert response.rad is None
                    assert response.lyr is None
                case 'all':
                    assert isinstance(response.cfg, PyConfig)
                    assert isinstance(response.rad, PyRad)
                    assert isinstance(response.lyr, PyLyr)
                    assert isinstance(response.noi, PyRad)
                case 'upd':
                    assert response.cfg is None
                    assert response.rad is None
                    assert response.lyr is None
                    assert response.noi is None
                case 'set':
                    assert response.cfg is None
                    assert response.rad is None
                    assert response.lyr is None
                    assert response.noi is None
                case None:
                    assert response.cfg is None
                    assert isinstance(response.rad, PyRad)
                    assert response.lyr is None
                    assert response.noi is None
            APICall(cfg=cfg, output_type='set', app=None, url=url)() # This should clean up
    
    # Test all combinations
    n_tested = 0
    for psg_running in is_psg_running:
        if psg_running:
            start_psg(strict=True)
        else:
            stop_psg(strict=False)
        for url_setting in url_settings:
            settings.save_settings(url=url_setting)
            for cfg in cfgs:
                for output_type in output_types:
                    for app in apps:
                        for url in urls:
                            n_tested += 1
                            try:
                                check(
                                    psg_running,
                                    cfg,
                                    output_type,
                                    app,
                                    url,
                                    url_setting
                                )
                            except Exception as e:
                                msg = f'Failed for\npsg_running={psg_running}\ncfg={cfg}\noutput_type={output_type}\napp={app}\nurl={url}\nurl_setting={url_setting}\nn_tested={n_tested}'
                                raise Exception(msg) from e


if __name__ in '__main__':
    pytest.main(args=[__file__])