"""
Tests for ExoCAM support.

If you are running this test locally, you will need to download the ExoCAM test dataset.
You can download it by running the below code:

.. code-block:: bash
    python -c "from pypsg.globes.exocam.exocam import download_test_data; download_test_data()"
"""
from os import chdir
from pathlib import Path
import logging
import pytest
import numpy as np
from astropy import units as u

import netCDF4 as nc

from libpypsg.globes.exocam.exocam import validate_variables, get_time_index, TIME_UNIT,get_shape
import libpypsg.globes.exocam.exocam as rw
from libpypsg.globes.exocam import download_exocam_test_data
from libpypsg.globes import PyGCM, exocam_to_pygcm
from libpypsg.globes import structure
from libpypsg import PyConfig, APICall
from libpypsg.cfg import models


chdir(Path(__file__).parent)

LOG_PATH = Path(__file__).parent / 'logs' / 'exocam.log'
if not LOG_PATH.parent.exists():
    LOG_PATH.parent.mkdir()

log = logging.Logger('exocam')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOG_PATH,mode='w')
fh.setLevel(logging.DEBUG)
log.addHandler(fh)

@pytest.fixture()
def data_path():
    if rw.TEST_PATH.exists():
        pass
    else:
        download_exocam_test_data()
    return rw.TEST_PATH

def test_validate_vars(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        validate_variables(data)
    
def test_get_time_index(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        time = np.array(data.variables['time'][:])*TIME_UNIT
        for i,t in enumerate(time[:3]):
            assert get_time_index(data,t) == i
def test_get_shape(data_path):
    """
    Test that the shape of the variables is correct.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        shape = get_shape(data)
        assert data.variables['T'].shape == shape
def test_surface_pressure(data_path):
    """
    Test getting the surface pressure.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        ps = rw.get_psurf(data,0)
        _,_,N_lat,N_lon = get_shape(data)
        assert ps.shape == (N_lon,N_lat)
def test_pressure(data_path):
    """
    Test getting the pressure.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        press = rw.get_pressure(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert press.shape == (N_layer,N_lon,N_lat)
def test_tsurf(data_path):
    """
    Test getting the surface temperature.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        tsurf = rw.get_tsurf(data,0)
        _,_,N_lat,N_lon = get_shape(data)
        assert tsurf.shape == (N_lon,N_lat)
def test_temperature(data_path):
    """
    Test getting the temperature.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        temp = rw.get_temperature(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert temp.shape == (N_layer,N_lon,N_lat)
def test_get_winds(data_path):
    """
    Test getting the winds.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        U,V = rw.get_winds(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert U.shape == (N_layer,N_lon,N_lat)
        assert V.shape == (N_layer,N_lon,N_lat)

def test_albedo(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        albedo = rw.get_albedo(data,0)
        _,_,N_lat,N_lon = get_shape(data)
        assert albedo.shape == (N_lon,N_lat)
def test_aerosol(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        _,N_layer,N_lat,N_lon = get_shape(data)
        water = rw.get_aerosol(data,0,'Water')
        water_size = rw.get_aerosol_size(data,0,'Water')
        assert water.shape == (N_layer,N_lon,N_lat)
        assert water_size.shape == (N_layer,N_lon,N_lat)
        ice = rw.get_aerosol(data,0,'WaterIce')
        ice_size = rw.get_aerosol_size(data,0,'WaterIce')
        assert ice.shape == (N_layer,N_lon,N_lat)
        assert ice_size.shape == (N_layer,N_lon,N_lat)
def test_molecules(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        h2o = rw.get_molecule(data,0,'H2O',mean_molecular_mass=18.02)
        # _,N_layer,N_lat,N_lon = get_shape(data)
        # assert co2.dat.shape == (N_layer,N_lat,N_lon)
        molecs = rw.get_molecule_suite(data,0,['H2O'],background='N2',mean_molecular_mass=28.01)
        for molec in molecs:
            assert isinstance(molec, structure.Molecule)
        with pytest.raises(ValueError):
            _ = rw.get_molecule(data,0,'H2O',mean_molecular_mass=None)
        

def test_write_cfg_params(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        gcm = rw.to_pygcm(
            data=data,
            itime=0,
            molecules=['H2O'],
            aerosols=['Water'],
            mean_molecular_mass=28.01
        )
    assert isinstance(gcm,PyGCM)
    atmosphere = gcm.update_params(None)
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
    
    pycfg = PyConfig(gcm=gcm)
    content = pycfg.content
    assert b'<ATMOSPHERE-NAERO>1' in content
    assert b'<ATMOSPHERE-GAS>H2O' in content
    assert b'<ATMOSPHERE-NGAS>1' in content

def test_call_psg(data_path,psg_url):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        gcm = exocam_to_pygcm(
            data,
            itime=0,
            molecules=['H2O','CO2'],
            aerosols=['Water'],
            mean_molecular_mass=28.01
        )
        tele = models.SingleTelescope(
            fov = 5*u.arcsec
        )
        geo = models.Observatory(observer_altitude = 1.3*u.pc,)
        obj = models.Target(name = 'Exoplanet', object='Exoplanet',diameter=1*u.R_earth,season=30*u.deg)
        gen = models.Generator(gcm_binning=200)
        cfg = PyConfig(gcm=gcm,telescope=tele,geometry=geo,target=obj,generator=gen)
        psg = APICall(cfg,'all','globes',url=psg_url,logger=log)
        psg.reset()
        try:
            response = psg()
            psg.reset()
        except Exception as e:
            with open(LOG_PATH, 'rt', encoding='UTF-8') as file:
                raise Exception(file.read()) from e
            
        assert not np.any(np.isnan(response.lyr.prof['H2O']))
        assert not np.any(np.isnan(response.lyr.prof['CO2']))
        assert np.all(response.lyr.prof['CO2']==response.lyr.prof['CO2'][0])

if __name__ in '__main__':
    pytest.main(args=[__file__])