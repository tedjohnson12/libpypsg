import pytest
from astropy import units as u

from pypsg import units

def test_ppmv():
    abn = 100*units.ppmv
    assert abn.to_value(u.dimensionless_unscaled) == pytest.approx(1e-4,abs=1e-7)
def test_ppbv():
    abn = 1*units.ppbv
    assert abn.to_value(u.dimensionless_unscaled) == pytest.approx(1e-9,abs=1e-12)
def test_pptv():
    abn = 1*units.pptv
    assert abn.to_value(u.dimensionless_unscaled) == pytest.approx(1e-12,abs=1e-12)