"""
Test the user interface
"""
import pytest
import requests
from pathlib import Path

from pypsg.cfg import PyConfig, BinConfig, models
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
                            

class TestPyConfig:
    """
    Test user interaction with the PyConfig class
    """
    
    def test_init(self):
        """
        Test the initialization of the PyConfig class
        
        Parameters
        ----------
        target : models.Target
            Target object
        geometry : models.Geometry
            Geometry object
        atmosphere : models.Atmosphere
            Atmosphere object
        surface : models.Surface
            Surface object
        generator : models.Generator
            Generator object
        telescope : models.Telescope
            Telescope object
        noise : models.Noise
            Noise object
        gcm : globes.GCM
            GCM object
        
        Expectations
        ------------
        Each argument will either be kept as is or (in the case where None is passed),
        replaced with the default (empty) version of the Model.
        
        The exception is for `gcm`, which is kept as is always.
        """
        # Case where everything is None
        cfg = PyConfig()
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.content == b'', f'Target content is {cfg.target.content}'
        assert isinstance(cfg.geometry, models.Geometry), f'Geometry is {type(cfg.geometry)}'
        assert cfg.geometry.content == b'', f'Geometry content is {cfg.geometry.content}'
        assert isinstance(cfg.atmosphere, models.Atmosphere), f'Atmosphere is {type(cfg.atmosphere)}'
        assert cfg.atmosphere.content == b'', f'Atmosphere content is {cfg.atmosphere.content}'
        assert isinstance(cfg.surface, models.Surface), f'Surface is {type(cfg.surface)}'
        assert cfg.surface.content == b'', f'Surface content is {cfg.surface.content}'
        assert isinstance(cfg.generator, models.Generator), f'Generator is {type(cfg.generator)}'
        assert cfg.generator.content == b'', f'Generator content is {cfg.generator.content}'
        assert isinstance(cfg.telescope, models.Telescope), f'Telescope is {type(cfg.telescope)}'
        assert cfg.telescope.content == b'', f'Telescope content is {cfg.telescope.content}'
        assert isinstance(cfg.noise, models.Noise), f'Noise is {type(cfg.noise)}'
        assert cfg.noise.content == b'', f'Noise content is {cfg.noise.content}'
        assert cfg.gcm is None, f'GCM is {type(cfg.gcm)}'
        
        # Case with Target
        cfg = PyConfig(target=models.Target(object='Exoplanet',name='earth',))
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.object.value == 'Exoplanet'
        assert cfg.target.name.value == 'earth'
        assert cfg.target.date.value is None
        
        # Case with Geometry
        # TODO: Add more tests
        

if __name__ in '__main__':
    pytest.main(args=[__file__])