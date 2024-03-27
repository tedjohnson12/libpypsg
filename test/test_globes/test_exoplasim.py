"""
Tests for exoplasim module.

If you are running this test locally, you will need to download the ExoPlasim test dataset.

.. code-block:: bash
    python -c "from pypsg.globes.exoplasim.exoplasim import download_test_data; download_test_data()"
"""

from netCDF4 import Dataset
import pytest
import numpy as np
from astropy import units as u
from pypsg.globes import PyGCM
from pypsg.cfg import PyConfig, models
from pypsg import APICall


from pypsg.globes.exoplasim.exoplasim import (
    get_shape,
    TEST_PATH,
    get_psurf,
    get_pressure,
    get_temperature,
    get_tsurf,
    get_winds,
    get_albedo,
    get_emissivity,
    get_molecule,
    get_aerosol,
    get_aerosol_size,
    get_molecule_suite,
    to_pygcm
)

@pytest.fixture
def data()->Dataset:
    with Dataset(TEST_PATH) as _data:
        yield _data

def test_get_shape(data):
    """
    Test that the shape is found correctly.
    """
    n_time, n_layers, n_lat, n_lon = get_shape(data)
    assert n_time == 12
    assert n_layers == 20
    assert n_lat == 64
    assert n_lon == 128

def test_get_psurf(data):
    """
    Test that the surface pressure is found correctly.
    """
    ps = get_psurf(data,0)
    assert ps.dat.unit.physical_type == 'pressure'
    assert ps.dat.ndim == 2

def test_get_pressure(data):
    """
    Test that the pressure is found correctly.
    """
    _, n_layers, n_lat, n_lon = get_shape(data)
    press = get_pressure(data,0)
    assert press.dat.unit.physical_type == 'pressure'
    assert press.dat.ndim == 3
    assert press.dat.shape == (n_layers,n_lon,n_lat)
    press_at_surf = press.dat[0,:,:].to_value(u.bar)
    psurf = get_psurf(data,0).dat.to_value(u.bar)
    assert np.allclose(psurf,press_at_surf,rtol=0.1)

def test_temperature(data):
    """
    Test that the temperature is found correctly.
    """
    _, n_layers, n_lat, n_lon = get_shape(data)
    temp = get_temperature(data,0)
    assert temp.dat.unit.physical_type == 'temperature'
    assert temp.dat.ndim == 3
    assert temp.dat.shape == (n_layers,n_lon,n_lat)

def test_get_tsurf(data):
    """
    Test that the surface temperature is found correctly.
    """
    tsurf = get_tsurf(data,0)
    assert tsurf.dat.unit.physical_type == 'temperature'
    assert tsurf.dat.ndim == 2
    t_at_surface = get_temperature(data,0).dat[0,:,:].to_value(u.K)
    tsurf = tsurf.dat.to_value(u.K)
    assert np.allclose(tsurf,t_at_surface,rtol=0.2)

def test_get_winds(data):
    """
    Test that the winds are found correctly.
    """
    U,V = get_winds(data,0)
    assert U.dat.unit.physical_type == 'velocity'
    assert U.dat.ndim == 3
    assert U.dat.shape == (20,128,64)
    assert V.dat.unit.physical_type == 'velocity'
    assert V.dat.ndim == 3
    assert V.dat.shape == (20,128,64)

def test_get_albedo(data):
    """
    Test that the albedo is found correctly.
    """
    alb = get_albedo(data,0)
    assert alb.dat.unit.physical_type == 'dimensionless'
    assert alb.dat.ndim == 2
    assert alb.dat.shape == (128,64)
    assert np.all(alb.dat <= 1.0) & np.all(alb.dat >= 0.0)

def test_get_emissivity(data):
    """
    Test that the emissivity is found correctly.
    
    For now, it is just a placeholder.
    """
    with pytest.raises(NotImplementedError):
        get_emissivity(data,0)

def test_get_molecule(data):
    """
    Test that the molecules are found correctly.
    """
    h2o = get_molecule(data,0,'H2O',mean_molecular_mass=18.02)
    assert h2o.dat.unit.physical_type == 'dimensionless'
    assert h2o.dat.ndim == 3
    assert h2o.dat.shape == (20,128,64)
    assert np.all(h2o.dat <= 1.0) & np.all(h2o.dat >= 0.0)
    with pytest.raises(ValueError):
        _ = get_molecule(data,0,'H2O',mean_molecular_mass=None)
    
def test_get_aerosol(data):
    """
    Test that the aerosol is found correctly.
    """
    water = get_aerosol(data,0,'Water')
    assert water.dat.unit.physical_type == 'dimensionless'
    assert water.dat.ndim == 3
    assert water.dat.shape == (20,128,64)
    assert np.all(water.dat <= 1.0) & np.all(water.dat >= 0.0)

def test_get_aerosol_size(data):
    """
    Test that the aerosol size is found correctly.
    """
    water_size = get_aerosol_size(data,0,'Water')
    assert water_size.dat.unit.physical_type == 'length'
    assert water_size.dat.ndim == 3
    assert water_size.dat.shape == (20,128,64)
    assert np.all(water_size.dat == water_size.dat[0,0,0])

def test_get_molecule_suite(data):
    """
    Test that the molecules are found correctly.
    """
    mols = get_molecule_suite(data,0,['H2O'],None,28.0)
    assert mols[0].name == 'H2O'
    assert len(mols) == 1
    mols = get_molecule_suite(data,0,['H2O'],'N2',28.0)
    assert tuple(m.name for m in mols) == ('H2O','N2')
    with pytest.raises(ValueError):
        _ = get_molecule_suite(data,0,['H2O'],None,None)
    with pytest.raises(ValueError):
        _ = get_molecule_suite(data,0,['H2O'],'H2O',28.1)

def test_to_pygcm(data):
    """
    Test that the pygcm interface works correctly.
    """
    pygcm = to_pygcm(
        data,
        0,
        ['H2O'],
        ['Water'],
        mean_molecular_mass=28.01
    )
    assert isinstance(pygcm, PyGCM)
    
    atmosphere = pygcm.update_params(None)
    assert atmosphere.description.value is not None
    assert atmosphere.molecules._ngas == 1
    assert atmosphere.molecules._value[0].name == 'H2O'
    assert atmosphere.aerosols._naero == 1
    assert atmosphere.aerosols._value[0].name == 'Water'
    cfg = atmosphere.content
    assert cfg != b''
    # assert b'<ATMOSPHERE-LAYERS>' + str(nlayers).encode('utf-8') in cfg
    assert b'<ATMOSPHERE-NAERO>1' in cfg
    assert b'<ATMOSPHERE-GAS>H2O' in cfg
    assert b'<ATMOSPHERE-NGAS>1' in cfg
    
    pycfg = PyConfig(gcm=pygcm)
    content = pycfg.content
    assert b'<ATMOSPHERE-NAERO>1' in content
    assert b'<ATMOSPHERE-GAS>H2O' in content
    assert b'<ATMOSPHERE-NGAS>1' in content

def test_call_psg(data,psg_url):
    """
    Test to make sure a PSG call works.
    """
    gcm = to_pygcm(
        data,
        itime=0,
        molecules=['H2O'],
        aerosols=['Water'],
        mean_molecular_mass=28.01
    )
    tele = models.SingleTelescope(
        fov = 5*u.arcsec
    )
    geo = models.Observatory(observer_altitude = 1.3*u.pc,)
    obj = models.Target(name = 'Exoplanet', object='Exoplanet',diameter=1*u.R_earth,season=30*u.deg)
    cfg = PyConfig(gcm=gcm,telescope=tele,geometry=geo,target=obj)
    psg = APICall(cfg,'all','globes',url=psg_url)
    psg.reset()
    response = psg()
    assert not np.any(np.isnan(response.lyr.prof['H2O']))
        
    
    
if __name__ == '__main__':
    pytest.main(args=[__file__])