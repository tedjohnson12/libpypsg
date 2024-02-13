"""
Tests for WACCM support.

If you are running this test locally, you will need to download the WACCM test dataset.
You can download it by running ``VSPEC.builtins.download_waccm_test_data()``, for example:

.. code-block:: bash
    python -c "from pypsg.globes.waccm.waccm import download_test_data; download_test_data()"
"""
from os import chdir
from pathlib import Path
import pytest
import numpy as np

import netCDF4 as nc

from pypsg.globes.exocam.exocam import validate_variables, get_time_index, TIME_UNIT,get_shape
import pypsg.globes.exocam.exocam as rw
from pypsg.globes import PyGCM
from pypsg.globes import structure


chdir(Path(__file__).parent)

@pytest.fixture()
def data_path():
    if rw.TEST_PATH.exists():
        return rw.TEST_PATH
    else:
        return rw.TEST_URL

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
        assert ps.shape == (N_lat,N_lon)
def test_pressure(data_path):
    """
    Test getting the pressure.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        press = rw.get_pressure(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert press.shape == (N_layer,N_lat,N_lon)
def test_tsurf(data_path):
    """
    Test getting the surface temperature.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        tsurf = rw.get_tsurf(data,0)
        _,_,N_lat,N_lon = get_shape(data)
        assert tsurf.shape == (N_lat,N_lon)
def test_temperature(data_path):
    """
    Test getting the temperature.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        temp = rw.get_temperature(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert temp.shape == (N_layer,N_lat,N_lon)
def test_get_winds(data_path):
    """
    Test getting the winds.
    """
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        U,V = rw.get_winds(data,0)
        _,N_layer,N_lat,N_lon = get_shape(data)
        assert U.shape == (N_layer,N_lat,N_lon)
        assert V.shape == (N_layer,N_lat,N_lon)

def test_albedo(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        albedo = rw.get_albedo(data,0)
        _,_,N_lat,N_lon = get_shape(data)
        assert albedo.shape == (N_lat,N_lon)
def test_aerosol(data_path):
    with nc.Dataset(data_path,'r',format='NETCDF4') as data:
        _,N_layer,N_lat,N_lon = get_shape(data)
        water = rw.get_aerosol(data,0,'Water')
        water_size = rw.get_aerosol_size(data,0,'Water')
        assert water.shape == (N_layer,N_lat,N_lon)
        assert water_size.shape == (N_layer,N_lat,N_lon)
        ice = rw.get_aerosol(data,0,'WaterIce')
        ice_size = rw.get_aerosol_size(data,0,'WaterIce')
        assert ice.shape == (N_layer,N_lat,N_lon)
        assert ice_size.shape == (N_layer,N_lat,N_lon)
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
            aerosols=None,
            mean_molecular_mass=28.01
        )
    assert isinstance(gcm,PyGCM)

if __name__ in '__main__':
    pytest.main(args=[__file__])