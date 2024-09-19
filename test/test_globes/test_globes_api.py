"""
API tests for GlobES
"""
import logging
from pathlib import Path
import time
import numpy as np
import pytest
from astropy import units as u
from libpypsg.globes import PyGCM, structure, GCMdecoder
from libpypsg import PyConfig, APICall
from libpypsg.cfg import models

LOG_PATH = Path(__file__).parent / 'logs' / 'globes.log'
log = logging.getLogger('globes')
fh = logging.FileHandler(LOG_PATH)
fh.setLevel(logging.DEBUG)
log.addHandler(fh)
log.setLevel(logging.DEBUG)


class TestPyGCM:
    def test_init(self):
        """
        Test initialization for the PyGCM class
        
        Scenarios
        ---------
        * Only pressure specified
        * Wind specified
        * Pressure and Temperature specified
        * Pressure, Temperature, and a molecule specified
        * Pressure is not specified
        * All variables specified
        
        Checks
        ------
        * There is a value for wind always.
        * Check the header
        * Check the dtype of the data
        * Molecules
        * Aerosols
        * Aerosol sizes
        * Changes to the config
        """
        
        pressure = structure.Pressure.from_limits(1*u.bar,1e-5*u.bar,(10,10,10))
        temperature = structure.Temperature.from_adiabat(
            1.0, structure.SurfaceTemperature(300*u.K*np.ones((10,10))), pressure
        )
        pygcm = PyGCM(pressure,temperature)
        assert pygcm.wind_u.dat.shape == (10,10,10)
        assert pygcm.wind_v.dat.shape == (10,10,10)
        assert 'Wind' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        assert pygcm.flat.size == 4*10*10*10
        assert pygcm.molecules == []
        assert pygcm.aerosols == []
        assert pygcm.aerosol_sizes == []
        
        wind_u = structure.Wind.constant('wind_u', 0*u.m/u.s, (10,10,10))
        wind_v = structure.Wind.constant('wind_v', 0*u.m/u.s, (10,10,10))
        pygcm = PyGCM(pressure,temperature, wind_u, wind_v)
        assert 'Wind' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        assert np.all(pygcm.flat == PyGCM(pressure,temperature).flat)
        with pytest.warns(RuntimeWarning):
            _ = structure.Wind.constant('U', 0*u.m/u.s, (10,10,10))
        
        pygcm = PyGCM(pressure, temperature)
        assert 'Temperature' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        
        h2o = structure.Molecule.constant('H2O', 1e-5*u.dimensionless_unscaled, (10,10,10))
        pygcm = PyGCM(pressure,temperature, h2o)
        assert 'Pressure' in pygcm.header
        assert 'Temperature' in pygcm.header
        assert 'H2O' in pygcm.header
        assert pygcm.molecules[0].name == 'H2O'
        cfg = pygcm.update_params()
        assert cfg.molecules.value[0].name == 'H2O'
    
    def test_to_psg(self,psg_url):
        nlayer = 10
        nlon = 30
        nlat = 20
        shape = (nlayer, nlon, nlat)
        wind_u = structure.Wind.constant('wind_u', 1*u.m/u.s,shape)
        wind_v = structure.Wind.constant('wind_v', -1*u.m/u.s,shape)
        pressure = structure.Pressure.from_profile(10.**(-np.arange(nlayer))*u.bar, (nlon,nlat))
        
        lat = np.linspace(-90, 90, nlat)
        near_eq_lat = np.abs(lat) < 10
        lons = np.linspace(0, 360, nlon)
        near_int_date_line = np.abs(lons-180) < 30
        tsurf = np.ones((nlon,nlat))*300*u.K
        tsurf[:,near_eq_lat] = 280*u.K
        tsurf[near_int_date_line,:] = 320*u.K
        
        surface_pressure = structure.SurfacePressure.from_pressure(pressure)
        surface_temperature = structure.SurfaceTemperature(tsurf)
        temperature = structure.Temperature.from_adiabat(1.0, surface_temperature, pressure)
        albedo = structure.Albedo.constant(0.5, (nlon,nlat))
        co2 = structure.Molecule.constant('CO2', 1e-5, shape)
        pygcm = PyGCM(pressure, temperature, co2, wind_u=wind_u, wind_v=wind_v,
                       psurf=surface_pressure, tsurf=surface_temperature,
                       albedo=albedo)
        tele = models.SingleTelescope(
            fov = 5*u.arcsec
        )
        geo = models.Observatory(observer_altitude = 1.3*u.pc,)
        obj = models.Target(name = 'Exoplanet', object='Exoplanet',diameter=1*u.R_earth,season=30*u.deg,star_distance=0.05*u.AU)
        cfg = PyConfig(gcm=pygcm,telescope=tele,geometry=geo,target=obj)
        psg = APICall(cfg,'all','globes',url=psg_url)
        decoder = GCMdecoder.from_psg(cfg.content)
        assert decoder['Winds'].shape == (2,nlayer, nlon, nlat)
        psg.reset()
        time.sleep(0.1)
        try:
            response = psg()
            psg.reset()
        except Exception as e:
            with open(LOG_PATH, 'rt', encoding='UTF-8') as file:
                raise Exception(file.read()) from e
        assert not np.any(np.isnan(response.lyr.prof['CO2']))
    
        

if __name__ == '__main__':
    pytest.main([__file__])
        