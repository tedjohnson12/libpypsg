"""
API tests for GlobES
"""
import numpy as np
import pytest
from astropy import units as u
from pypsg.globes import PyGCM, structure

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
        pygcm = PyGCM(pressure)
        assert pygcm.wind_u.dat.shape == (10,10,10)
        assert pygcm.wind_v.dat.shape == (10,10,10)
        assert 'Wind' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        assert pygcm.flat.size == 3*10*10*10
        assert pygcm.molecules == []
        assert pygcm.aerosols == []
        assert pygcm.aerosol_sizes == []
        
        wind_u = structure.Wind.contant('wind_u', 0*u.m/u.s, (10,10,10))
        wind_v = structure.Wind.contant('wind_v', 0*u.m/u.s, (10,10,10))
        pygcm = PyGCM(pressure, wind_u, wind_v)
        assert 'Wind' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        assert np.all(pygcm.flat == PyGCM(pressure).flat)
        with pytest.warns(RuntimeWarning):
            _ = structure.Wind.contant('U', 0*u.m/u.s, (10,10,10))
        
        tsurf = structure.SurfaceTemperature(np.ones((10,10))*300*u.K)
        temperature = structure.Temperature.from_adiabat(1.4, tsurf, pressure)
        pygcm = PyGCM(pressure, temperature)
        assert 'Temperature' in pygcm.header
        assert 'Pressure' in pygcm.header
        assert pygcm.flat.dtype == np.float32
        
        h2o = structure.Molecule.constant('H2O', 1e-5, (10,10,10))
        pygcm = PyGCM(pressure,temperature, h2o)
        assert 'Pressure' in pygcm.header
        assert 'Temperature' in pygcm.header
        assert 'H2O' in pygcm.header
        assert pygcm.molecules[0].name == 'H2O'
        cfg = pygcm.update_params()
        assert cfg.molecules.value[0].name == 'H2O'
        

if __name__ == '__main__':
    pytest.main([__file__])
        