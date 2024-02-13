"""
Test the user interface
"""
from pathlib import Path
import pytest
import requests
from astropy import units as u
import time

from pypsg.cfg import PyConfig, BinConfig, models
from pypsg import settings
from pypsg.globes import globes
from pypsg.exceptions import GlobESError, PSGMultiError
from pypsg.settings import INTERNAL_PSG_URL, PSG_URL
from pypsg.docker import start_psg, stop_psg, is_psg_installed
from pypsg import APICall, PSGResponse, PyRad, PyLyr

TR1e_PATH = Path(__file__).parent / 'test_cfg' / 'data' / 'TR1e_mirecle.cfg'

@pytest.fixture
def keep_psg_settings():
    """
    Make sure my PSG settings don't change after running tests.
    Otherwise I could not test different settings.
    """
    orginal_url = settings.get_setting('url')
    yield None
    settings.save_settings(url=orginal_url)
    
@pytest.fixture
def temp_file():
    """
    Get a temporary file name and make sure it gets deleted.
    """
    file_path = Path(__file__).parent / 'temp.txt'
    yield file_path
    file_path.unlink(missing_ok=True)

@pytest.mark.slow
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
        The app to use. Either None of 'globes'. We will just test None for now.
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
    apps = [None]
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
                time.sleep(0.1)
                _ = api()
        elif expect_globes_err:
            with pytest.raises((GlobESError,PSGMultiError)):
                _ = api()
            APICall(cfg=cfg, output_type='set', app=None, url=url)() # This should clean up
        else:
            time.sleep(0.1)
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
            # APICall(cfg=cfg, output_type='set', app=None, url=url)() # This should clean up
    
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
        cfg = PyConfig(geometry=models.Observatory(stellar_type='M'))
        assert isinstance(cfg.geometry, models.Geometry), f'Geometry is {type(cfg.geometry)}'
        assert cfg.geometry.stellar_type.value == 'M'
        assert cfg.geometry.geometry.value == 'Observatory'
        assert cfg.geometry.ref.value is None
        
        # Case with Atmosphere
        cfg = PyConfig(atmosphere=models.EquilibriumAtmosphere(pressure=1*u.bar))
        assert isinstance(cfg.atmosphere, models.Atmosphere), f'Atmosphere is {type(cfg.atmosphere)}'
        assert cfg.atmosphere.structure.value == 'Equilibrium'
        assert cfg.atmosphere.pressure.value == 1*u.bar
        assert cfg.atmosphere.temperature.value is None
        
        # Case with Surface
        cfg = PyConfig(surface=models.Surface(temperature=100*u.K))
        assert isinstance(cfg.surface, models.Surface), f'Surface is {type(cfg.surface)}'
        assert cfg.surface.temperature.value == 100*u.K
        assert cfg.surface.albedo.value is None
        assert cfg.surface.emissivity.value is None
        
        # Case with Generator
        cfg = PyConfig(generator=models.Generator(gas_model=True))
        assert isinstance(cfg.generator, models.Generator), f'Generator is {type(cfg.generator)}'
        assert cfg.generator.gas_model.value is True
        assert cfg.generator.continuum_model.value is None
        
        # Case with Telescope
        cfg = PyConfig(telescope=models.SingleTelescope(apperture=10*u.m))
        assert isinstance(cfg.telescope, models.Telescope), f'Telescope is {type(cfg.telescope)}'
        assert cfg.telescope.telescope.value == 'SINGLE'
        assert cfg.telescope.apperture.value == 10*u.m
        assert cfg.telescope.zodi.value is None
        
        # Case with Noise
        cfg = PyConfig(noise=models.CCD(temperature=35*u.K))
        assert isinstance(cfg.noise, models.Noise), f'Noise is {type(cfg.noise)}'
        assert cfg.noise.noise_type.value == 'CCD'
        assert cfg.noise.temperature.value == 35*u.K
        assert cfg.noise.read_noise.value is None
        
        # Case with GCM
        cfg = PyConfig(gcm=globes.GCM('header',[1,2,3]))
        assert isinstance(cfg.gcm, globes.GCM), f'GCM is {type(cfg.gcm)}'
    
    def test_from_dict(self):
        """
        Test initalization from a dictionary.
        
        Parameters
        ----------
        d : dict
            A dictionary representation of a PSG config file.
            Under the hood, the actual dictionary is parsed
            by each field individually, but the user does not
            know or care about that.
        
        Considerations
        --------------
        * The dictionary has a single level of nesting.
        * Additional keys are ignored.
        * The dictionary is not validated.
        * Some fields use more than one key.
        * Any key that is lowercase will raise an error.
        """
        
        # Nominal case
        d = {'OBJECT-NAME': 'Earth', 'GEOMETRY': 'Observatory', 'GEOMETRY-OBS-ALTITUDE': 1.3, 'GEOMETRY-ALTITUDE-UNIT': 'pc'}
        cfg = PyConfig.from_dict(d)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'Earth'
        assert isinstance(cfg.geometry, models.Geometry), f'Geometry is {type(cfg.geometry)}'
        assert cfg.geometry.geometry.value == 'Observatory'
        assert cfg.geometry.observer_altitude.value == 1.3*u.pc
        
        # Extra key
        d = {'OBJECT-NAME': 'Earth', 'EXTRA': 'foo'}
        cfg = PyConfig.from_dict(d)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'Earth'
        
        # Missing key
        d = {'OBJECT-NAME': 'Earth', 'GEOMETRY': 'Observatory', 'GEOMETRY-OBS-ALTITUDE': 1.3}
        cfg = PyConfig.from_dict(d)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'Earth'
        assert isinstance(cfg.geometry, models.Geometry), f'Geometry is {type(cfg.geometry)}'
        assert cfg.geometry.geometry.value == 'Observatory'
        assert cfg.geometry.observer_altitude.value is None
        
        # Lowercase key
        d = {'object-name': 'Earth'}
        with pytest.raises(ValueError):
            _ = PyConfig.from_dict(d)
    
    def test_from_binaryconfig(self):
        """
        Test initalization from a binary config object.
        
        Parameters
        ----------
        bcfg : BinConfig
            A binary config object.
        """
        b = b'<OBJECT-NAME>Earth'
        cfg = PyConfig.from_binaryconfig(BinConfig(b))
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'Earth'
    
    def test_from_bytes(self):
        """
        Test initalization from a bytes object.
        
        Parameters
        ----------
        b : bytes
            A bytes object.
        
        Considerations
        --------------
        * The bytes object is not validated.
        * The bytes object is first read as a BinConfig, so it should
          be responsible for handling any errors.
        """
        b = b'<OBJECT-NAME>Earth'
        cfg = PyConfig.from_bytes(b)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'Earth'
    
    def test_from_file(self):
        """
        Test initalization from a file path.
        
        Parameters
        ----------
        path : Path | str
            A file path.
        """
        # pathlib.Path
        path = Path(__file__).parent / 'test_cfg' / 'data' / 'object_gj1214b.cfg'
        cfg = PyConfig.from_file(path)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'GJ 1214b'
        
        # str
        path = str(Path(__file__).parent / 'test_cfg' / 'data' / 'object_gj1214b.cfg')
        cfg = PyConfig.from_file(path)
        assert isinstance(cfg.target, models.Target), f'Target is {type(cfg.target)}'
        assert cfg.target.name.value == 'GJ 1214b'
    
    def test_content(self):
        """
        Test the `content` property.
        """
        
        cfg = PyConfig(target=models.Target(name='Earth'))
        assert cfg.content == b'<OBJECT-NAME>Earth'
        
    def test_tofile(self, temp_file:Path):
        """
        Test writing the config to a file.
        """
        
        cfg = PyConfig(target=models.Target(name='Earth'))
        cfg.to_file(temp_file)
        assert temp_file.read_text() == '<OBJECT-NAME>Earth'
        
        
        

if __name__ in '__main__':
    pytest.main(args=[__file__])