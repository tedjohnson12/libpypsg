

import pytest
from astropy import units as u

from pypsg.cfg.models import Target

def test_Target():
    target = Target(object='Exoplanet')
    assert target.object.value == b'Exoplanet'
    with pytest.raises(ValueError):
        _ = Target(object='Black Hole')