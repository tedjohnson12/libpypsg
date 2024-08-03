

import pytest

import numpy as np


from astropy import units as u
from pathlib import Path

from libpypsg.cfg.config import BinConfig
from libpypsg.cfg.base import Table
from libpypsg.cfg.models import Target, Geometry
from libpypsg.cfg.models import NoAtmosphere, EquilibriumAtmosphere, ComaAtmosphere

from libpypsg.cfg.models import (
    Surface,
    Generator,
    Telescope,
    SingleTelescope,
    Interferometer,
    Coronagraph,
    AOTF,
    LIDAR,
    Noise,
    Noiseless,
    RecieverTemperatureNoise,
    ConstantNoise,
    ConstantNoiseWithBackground,
    PowerEquivalentNoise,
    Detectability,
    CCD
)


def test_Target():
    target = Target(object='Exoplanet')
    assert target.object.asbytes == b'Exoplanet'
    with pytest.raises(ValueError):
        _ = Target(object='Black Hole')
    expected = b'<OBJECT>Exoplanet'
    assert target.content == expected
    
    path = Path(__file__).parent / 'data' / 'object_gj1214b.cfg'
    cfg = BinConfig.from_file(path)
    target:Target = Target.from_cfg(cfg.dict)
    assert target.object.asbytes == b'Exoplanet'
    assert target.name.asbytes == b'GJ 1214b'
    assert target.date.asbytes == b'2020/04/08 01:32'
    # pylint: disable-next:protected-access
    assert target.diameter._value == 35031.1 * u.km    

def test_Geometry():
    geo = Geometry(
        geometry='Observatory',
        obs_altitude = 1.3*u.pc
    )
    assert geo.geometry.asbytes == b'Observatory'
    expected = b'<GEOMETRY>Observatory\n'
    expected += b'<GEOMETRY-OBS-ALTITUDE>1.3000'

def test_NoAtmosphere():
    atm = NoAtmosphere()
    assert atm.structure._value == 'None'

def test_EquilibriumAtmosphere():
    atm = EquilibriumAtmosphere()
    assert atm.structure._value == 'Equilibrium'

def test_ComaAtmosphere():
    atm = ComaAtmosphere()
    assert atm.structure._value == 'Coma'

def test_surface():
    _ = Surface(
        temperature = 3000 * u.K,
        albedo = 0.5,
        emissivity = 0.5
    )

def test_generator():
    _ = Generator(
        resolution_kernel = True,
        gas_model = True,
        rad_units = u.Unit('W m-2 um-1')
    )

def test_telescope():
    _ = Telescope(
        telescope = 'SINGLE',
        apperture = 5 * u.m,
        fov = 1 * u.arcmin
    )

def test_single_telescope():
    _ = SingleTelescope(
        apperture = 5 * u.m,
        fov = 1 * u.arcmin
    )

def test_interferometer():
    _ = Interferometer(
        aperture = 5 * u.m,
        fov = 1 * u.arcmin,
        n_telescopes = 2
    )

def test_coronagraph():
    iwa = Table(
        x = np.array([1, 2, 3]),
        y = np.array([4, 5, 6])
    )
    _ = Coronagraph(
        aperture = 5 * u.m,
        fov = 1 * u.arcmin,
        iwa = iwa
    )
    
def test_aotf():
    _ = AOTF(
        aperture = 5 * u.m,
        fov = 1 * u.arcmin
    )

def test_lidar():
    _ = LIDAR(
        aperture = 5 * u.m,
        fov = 1 * u.arcmin
    )

def test_noise():
    _ = Noise(
        noise_type = 'CCD',
        exp_time = 1 * u.s,
        n_frames = 10,
    )

def test_noiseless():
    _ = Noiseless()

def test_reciever_temperature_noise():
    _ = RecieverTemperatureNoise(
        exp_time = 1 * u.s,
        temperature = 100 * u.K
    )

def test_constant_noise():
    _ = ConstantNoise(
        exp_time = 1 * u.s,
        sigma = 1
    )

def test_constant_noise_with_background():
    _ = ConstantNoiseWithBackground(
        exp_time = 1 * u.s,
        sigma = 1
    )

def test_power_equivalent_noise():
    _ = PowerEquivalentNoise(
        exp_time = 1 * u.s,
        sensitivity = 1 * u.W / u.Hz**(1/2)
    )

def test_detectability():
    _ = Detectability(
        sensitivity = 1 * u.cm * u.Hz**(1/2) / u.W,
        pixel_size = 1 * u.um
    )

def test_CCD():
    _ = CCD(
        exp_time = 1 * u.s,
        read_noise = 1 * u.electron,
        dark_current = Table(
            x = np.array([1, 2, 3])*u.um,
            y = np.array([4, 5, 6])*u.electron/u.s
        )
    )

    
    

if __name__ in '__main__':
    pytest.main([__file__])