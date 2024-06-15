"""
Tests for the trn module
"""
from pathlib import Path
import pytest
import numpy as np

from astropy import units as u

from pypsg import PyTrn


@pytest.fixture
def trn_path():
    """
    The path to the test data
    """
    return Path(__file__).parent / 'data' / 'speculoos3.trn'

def test_init(trn_path):
    """
    Test the initialization of the TRN class
    """
    trn = PyTrn.from_file(trn_path)
    assert isinstance(trn, PyTrn)
    assert isinstance(trn.wl, u.Quantity)
    assert isinstance(trn['Total'], u.Quantity)
    assert trn['Total'].unit == u.dimensionless_unscaled
    assert len(trn) > 1

if __name__ == '__main__':
    pytest.main(args=[__file__])
    