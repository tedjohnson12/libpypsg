

import pytest
from astropy import units as u

from pypsg.cfg.models import Target, Geometry
from pypsg.cfg.models import NoAtmosphere, EquilibriumAtmosphere, ComaAtmosphere

def test_Target():
    target = Target(object='Exoplanet')
    assert target.object.value == b'Exoplanet'
    with pytest.raises(ValueError):
        _ = Target(object='Black Hole')
    expected = b'<OBJECT>Exoplanet'
    assert target.content == expected

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
