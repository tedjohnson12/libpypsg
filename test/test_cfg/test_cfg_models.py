

import pytest
from astropy import units as u
from pathlib import Path

from pypsg.cfg.config import BinConfig

from pypsg.cfg.models import Target, Geometry
from pypsg.cfg.models import NoAtmosphere, EquilibriumAtmosphere, ComaAtmosphere


def test_Target():
    target = Target(object='Exoplanet')
    assert target.object.value == b'Exoplanet'
    with pytest.raises(ValueError):
        _ = Target(object='Black Hole')
    expected = b'<OBJECT>Exoplanet'
    assert target.content == expected
    
    path = Path(__file__).parent / 'data' / 'object_gj1214b.cfg'
    cfg = BinConfig.from_file(path)
    target = Target.from_cfg(cfg.dict)
    assert target.object.value == b'Exoplanet'
    assert target.name.value == b'GJ 1214b'
    assert target.date.value == b'2020/04/08 01:32'
    assert target.diameter._value == 35031.1 * u.km
    

def test_Geometry():
    geo = Geometry(
        geometry='Observatory',
        obs_altitude = 1.3*u.pc
    )
    assert geo.geometry.value == b'Observatory'
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

if __name__ in '__main__':
    pytest.main([__file__])