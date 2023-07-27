import pytest
from astropy import units as u

from pypsg.resources import units

def test_CFG_UNITS():
    for name, values in units.CFG_UNITS.items():
        assert isinstance(name,str)
        assert name == name.upper()
        assert isinstance(values,dict)
        assert 'unit' in values
        assert isinstance(values['unit'],str)
        _ = u.Unit(values['unit'])
        if 'fmt' in values:
            assert isinstance(values['fmt'],str)
            _ = f'{0.1:{values["fmt"]}}'