import pytest
from astropy import units as u

import pypsg as psg

def test_StringParam():
    p = psg.StringParam('object','Exoplanet')
    assert p.name == b'<OBJECT>'
    assert p.value == b'Exoplanet'
    assert p.content == b'<OBJECT>Exoplanet'
    
    with pytest.raises(TypeError):
        _ = psg.StringParam('object',4.0)

def test_QuantityParam():
    p = psg.QuantityParam('OBJECT-STAR-DISTANCE',1.0*u.AU)
    assert p.name == b'<OBJECT-STAR-DISTANCE>'
    assert p.value == b'1.00'
    assert p.content == b'<OBJECT-STAR-DISTANCE>1.00'
    
    p = psg.QuantityParam('object-star-distance',1.0*u.AU)
    assert p.name == b'<OBJECT-STAR-DISTANCE>'
    assert p.value == b'1.00'
    assert p.content == b'<OBJECT-STAR-DISTANCE>1.00'
    
    with pytest.raises(TypeError):
        _ = psg.QuantityParam('OBJECT-STAR-DISTANCE',1.0)
    with pytest.raises(KeyError):
        _ = psg.QuantityParam('FAKE-OBJECT',1.0*u.AU)
    with pytest.raises(u.UnitConversionError):
        _ = psg.QuantityParam('OBJECT-STAR-DISTANCE',1.0*u.s)



def test_Config():
    cfg = psg.Config(
        psg.StringParam('object','Exoplanet')
    )
    assert cfg.content == b'<OBJECT>Exoplanet'
    cfg = psg.Config(
        psg.StringParam('OBJECT','Exoplanet'),
        psg.StringParam('ATMOSPHERE-TYPE','Equilibrium')
    )
    assert cfg.content == b'<ATMOSPHERE-TYPE>Equilibrium\n<OBJECT>Exoplanet'
    cfg.set(psg.QuantityParam('OBJECT-STAR-DISTANCE',1.0*u.AU))
    assert b'OBJECT-STAR-DISTANCE' in cfg.content
    cfg.remove('OBJECT-STAR-DISTANCE')
    assert b'OBJECT-STAR-DISTANCE' not in cfg.content
    with pytest.raises(NameError):
        cfg.remove('FAKE-PARAM')
    cfg.remove('object')
    assert b'<OBJECT>' not in cfg.content
    cfg.remove(b'<ATMOSPHERE-TYPE>')
    assert cfg.content == b''