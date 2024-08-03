"""
VSPEC GCM structure
"""
from abc import ABC
import warnings
from astropy import units as u
from astropy.units.core import Unit
from astropy.units.quantity import Quantity


import numpy as np

DTYPE = 'float32'


class VariableAssumptionWarning(UserWarning):
    """
    A warning raised when a variable
    is not found in the netCDF file.
    """


class Variable(ABC):
    """
    The base class representing a GCM (General Circulation Model) variable.

    Parameters
    ----------
    name : str
        The name of the variable.
    psg_unit : astropy.units.Unit
        The unit assumed by the PSG GlobES app.
    dat : astropy.units.Quantity
        The data values of the variable as a `astropy.units.Quantity` object.

    Attributes
    ----------
    name : str
        The name of the variable.
    psg_unit : astropy.units.Unit
        The unit assumed by the PSG GlobES app.
    dat : astropy.units.Quantity
        The data values of the variable as a `astropy.units.Quantity` object.

    Methods
    -------
    flat() -> np.ndarray:
        Returns a flattened version of the data values of the variable as a
        NumPy array, with the physical unit converted to the specified `psg_unit`.
        The array is of dtype 'float32' and the flattening order is 'C'. This is the
        format in which PSG assumes GCM binaries are written.

    shape() -> Tuple[int]:
        Returns the shape of the data values of the variable as a tuple of integers.

    """

    def __init__(
        self,
        name: str,
        psg_unit: u.Unit,
        dat: u.Quantity
    ):
        if not isinstance(dat, u.Quantity):
            raise ValueError(
                f'dat must be a Quantity object, not {type(dat)}.')

        self.name = name
        self.psg_unit = psg_unit
        self.dat = dat

    @property
    def flat(self) -> np.ndarray:
        """
        Get a flattened version of the array.

        Returns a flattened version of the data values of the variable as a
        NumPy array, with the physical unit converted to the specified `psg_unit`.
        The array is of dtype 'float32' and the flattening order is 'C'. This is the
        format in which PSG assumes GCM binaries are written.

        Returns
        -------
        np.array
            The flattened array.
        """
        if self.dat.ndim == 1:
            return self.dat.to_value(self.psg_unit).astype(DTYPE).flatten('C')
        if self.dat.ndim == 2:
            axes = (0, 1)
            return np.swapaxes(self.dat.to_value(self.psg_unit).astype(DTYPE), *axes).flatten('C')
            # return self.dat.to_value(self.psg_unit).T[:,::-1].astype(DTYPE).flatten('C')
        else:
            axes = (1, 2)
        return np.swapaxes(self.dat.to_value(self.psg_unit).astype(DTYPE), *axes).flatten('C')

    @property
    def shape(self) -> tuple:
        """
        Get the shape of the data.

        Returns
        -------
        tuple
            The shape of the data.
        """
        return self.dat.shape


class Variable2D(Variable):
    """
    Variable subclass for 2D variables.
    """

    def __init__(self, name: str, psg_unit: Unit, dat: Quantity):
        if not dat.ndim == 2:
            raise ValueError(f'dat must have a shape of 2, not {dat.ndim}.')
        super().__init__(name, psg_unit, dat)


class Variable3D(Variable):
    """
    Variable subclass for 3D variables.
    """

    def __init__(self, name: str, psg_unit: Unit, dat: Quantity):
        if not dat.ndim == 3:
            raise ValueError(f'dat must have a shape of 3, not {dat.ndim}.')
        super().__init__(name, psg_unit, dat)


class Wind(Variable3D):
    """
    A subclass of Variable representing wind of a planet.

    Parameters
    ----------
    name : str
        The name of the wind variable. Usually either 'U' or 'V'.
    dat : astropy.units.Quantity
        The data values of the wind variable as a `astropy.units.Quantity` object.

    Attributes
    ----------
    name : str
        The name of the wind variable.
    psg_unit : astropy.units.Unit
        The physical unit of the wind variable, which is set to 'm s-1' for wind variables.
    dat : astropy.units.Quantity
        The data values of the wind variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, name: str, dat: u.Quantity):
        if name not in ['wind_u', 'wind_v']:
            msg = f'Wind variable name must be either "wind_u" or "wind_v", not {name}. '
            msg += 'This is to prevent confusion by the PyGCM `__setattr__` method, which assigns unknown variables based on name.'
            warnings.warn(msg, RuntimeWarning)
        super().__init__(name, u.Unit('m s-1'), dat)

    @classmethod
    def constant(
        cls,
        name: str,
        value: u.Quantity,
        shape: tuple
    ):
        """
        Creates a Wind object with constant wind values.

        Parameters
        ----------
        name : str
            The name of the wind variable.
        value : astropy.units.Quantity
            The constant value of the wind variable.
        shape : tuple
            The shape of the wind variable data array.

        Returns
        -------
        Wind:
            A Wind object with constant wind values specified by the given `value` and `shape`.
        """

        dat = np.ones(shape=shape)*value
        return cls(name, dat)

    @classmethod
    def zero(cls, name, shape):
        """
        Creates a Wind object with zero wind values.

        Parameters
        ----------
        name : str
            The name of the wind variable.
        shape : tuple
            The shape of the wind variable data array.

        Returns
        -------
        Wind
            A Wind object with zero wind values specified by the given `shape`.
        """

        dat = np.zeros(shape=shape)
        return cls(name, dat*u.Unit('m s-1'))


class Pressure(Variable3D):
    """
    A subclass of `Variable` representing pressure of a planet.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The data values of the pressure variable as a `astropy.units.Quantity` object.

    Attributes
    ----------
    name : str
        The name of the pressure variable, which is set to 'Pressure'.
    psg_unit : astropy.units.Unit
        The physical unit of the pressure variable, which is set to a logarithmic unit of 'bar' using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the pressure variable as a `astropy.units.Quantity` object.


    """

    def __init__(self, dat: u.Quantity):
        super().__init__('Pressure', u.LogUnit(u.bar), dat)

    @property
    def flat(self):
        return super().flat

    @classmethod
    def from_profile(cls, profile: u.Quantity, shape: tuple):
        """
        Creates a Pressure object with pressure values from a profile.

        Parameters
        ----------
        profile : astropy.units.Quantity
            The profile of pressure values for each layer.
        shape : tuple
            The shape of the pressure variable data array.

        Returns
        -------
        Pressure:
            A Pressure object with pressure values specified by the given `profile` and `shape`.
        """

        n_layers = len(profile)
        shape = (n_layers,) + shape
        dat = np.ones(shape=shape) * profile[:, np.newaxis, np.newaxis]
        return cls(dat)

    @classmethod
    def from_limits(
        cls,
        high: u.Quantity,
        low: u.Quantity,
        shape: tuple
    ):
        """
        Creates a Pressure object with pressure values between specified high and low limits.

        Parameters
        ----------
        high : astropy.units.Quantity
            The pressure at the planet surface
        low : astropy.units.Quantity
            The lowest pressure to include in the atmosphere.
        shape : tuple
            The shape of the pressure variable data array.

        Returns
        -------
        Pressure:
            A `Pressure` object with pressure values between the specified
            `high` and `low` limits, with the given `shape`.
        """

        n_layers = shape[0]
        shape2d = shape[1:]
        log_high = np.log10(high.to_value(u.bar))
        log_low = np.log10(low.to_value(u.bar))
        profile = np.logspace(log_high, log_low, n_layers)*u.bar
        return cls.from_profile(profile, shape2d)

    def get_adiabatic_scalar(self, gamma: float) -> np.ndarray:
        """
        Calculates the adiabatic scalar for the pressure variable using a specified gamma value.

        Parameters
        ----------
        gamma : float
            The value of gamma, representing the ratio of specific heats.

        Returns
        -------
        np.ndarray
            The adiabatic scalar as a function of pressure. Multiplying this
            array by the surface temperature will give the temperature at every
            GCM point.
        """
        p_surf = self.dat[0, :, :]
        relative_pressure = (
            self.dat/p_surf[np.newaxis, :, :]).to_value(u.dimensionless_unscaled)
        power = 1 - (1/gamma)
        return relative_pressure ** power


class SurfacePressure(Variable2D):
    """
    A subclass of Variable representing the surface pressure of a planet.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The surface pressure of the planet at every point.

    Attributes
    ----------
    name : str
        The name of the surface pressure variable, which is set to 'Psurf'.
    psg_unit : astropy.units.Unit
        The physical unit of the surface pressure variable, which is set to a logarithmic unit of 'bar' using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the surface pressure variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, dat: u.Quantity):
        super().__init__('Psurf', u.LogUnit(u.bar), dat)

    @property
    def flat(self):
        return super().flat

    @classmethod
    def constant(cls, value: u.Quantity, shape: tuple):
        """
        Creates a SurfacePressure object with constant surface pressure values.

        Parameters
        ----------
        value : astropy.units.Quantity
            The constant value of the surface pressure.
        shape : tuple
            The shape of the surface pressure variable data array.

        Returns
        -------
        SurfacePressure
            A `SurfacePressure` object with constant surface pressure
            values specified by the given `value` and `shape`.
        """

        dat = np.ones(shape=shape)*value
        return cls(dat)

    @classmethod
    def from_pressure(cls, pressure: Pressure):
        """
        Creates a `SurfacePressure` object from a `Pressure` object.

        Parameters
        ----------
        pressure : Pressure
            The `Pressure` object from which to extract the surface pressure value.

        Returns
        -------
        SurfacePressure
            A `SurfacePressure` object with the surface pressure value extracted
            from the provided `Pressure` object.
        """

        dat = pressure.dat[0, :, :]
        return cls(dat)


class SurfaceTemperature(Variable2D):
    """
    A subclass of Variable representing the surface temperature of a planet.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The surface temperature of the planet at every point.

    Attributes
    ----------
    name : str
        The name of the surface temperature variable, which is set to 'Tsurf'.
    psg_unit : astropy.units.Unit
        The physical unit of the surface temperature variable, which is set to Kelvin (K) using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the surface temperature variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, dat: u.Quantity):
        super().__init__('Tsurf', u.K, dat)


class Temperature(Variable3D):
    """
    A subclass of Variable representing the temperature of a planet.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The temperature of the planet at every point.

    Attributes
    ----------
    name : str
        The name of the temperature variable, which is set to 'Temperature'.
    psg_unit : astropy.units.Unit
        The physical unit of the temperature variable, which is set to Kelvin (K) using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the temperature variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, dat: u.Quantity):
        super().__init__('Temperature', u.K, dat)

    @classmethod
    def from_adiabat(
        cls,
        gamma: float,
        tsurf: SurfacePressure,
        pressure: Pressure
    ):
        """
        Creates a Temperature object from an adiabatic profile.

        Parameters
        ----------
        gamma : float
            The adiabatic index.
        tsurf : SurfacePressure
            The surface pressure of the planet.
        pressure : Pressure
            The 3D pressure profile of the planet.

        Returns
        -------
        Temperature
            A Temperature object with the temperature values calculated from the adiabatic profile.
        """

        adiabatic_scale = pressure.get_adiabatic_scalar(gamma)
        dat = adiabatic_scale*tsurf.dat[np.newaxis, :, :]
        return cls(dat)


class Molecule(Variable3D):
    """
    A subclass of Variable representing a specific molecule concentration.

    Parameters
    ----------
    name : str
        The name of the molecule variable.
    dat : astropy.units.Quantity
        The concentration of the molecule at every point.

    Attributes
    ----------
    name : str
        The name of the molecule variable.
    psg_unit : astropy.units.Unit
        The physical unit of the molecule concentration, which is set to a logarithmic unit of 'mol mol-1' using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the molecule concentration as a `astropy.units.Quantity` object.


    """

    def __init__(self, name: str, dat: u.Quantity):
        dat = u.Quantity(dat)
        super().__init__(name, u.LogUnit(u.Unit('mol mol-1')), dat)

    @classmethod
    def constant(cls, name: str, val: u.Quantity, shape: tuple):
        """
        Creates a Molecule object with constant concentration values.

        Parameters
        ----------
        name : str
            The name of the molecule variable.
        val : astropy.units.Quantity
            The constant concentration value of the molecule.
        shape : tuple
            The shape of the molecule concentration data array.

        Returns
        -------
        Molecule
            A Molecule object with constant concentration values specified by the given name, value, and shape.
        """

        dat = val * np.ones(shape=shape)
        return cls(name, dat)


class Aerosol(Variable3D):
    """
    A subclass of Variable representing aerosol concentrations.

    Parameters
    ----------
    name : str
        The name of the aerosol variable.
    dat : astropy.units.Quantity
        The aerosol concentration at every point.

    Attributes
    ----------
    name : str
        The name of the aerosol variable.
    psg_unit : astropy.units.Unit
        The physical unit of the aerosol concentration, which is set to a logarithmic unit of 'kg kg-1' using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the aerosol concentration as a `astropy.units.Quantity` object.

    """

    def __init__(self, name: str, dat: u.Quantity):
        super().__init__(name, u.LogUnit(u.Unit('kg kg-1')), dat)

    @classmethod
    def constant(cls, name: str, val: u.Quantity, shape: tuple):
        """
        Creates an Aerosol object with constant aerosol concentration values.

        Parameters
        ----------
        name : str
            The name of the aerosol variable.
        val : astropy.units.Quantity
            The constant aerosol concentration value.
        shape : tuple
            The shape of the aerosol concentration data array.

        Returns
        -------
        Aerosol
            An Aerosol object with constant aerosol concentration values specified by the given name, value, and shape.
        """

        dat = np.ones(shape=shape) * val
        return cls(name, dat)

    @classmethod
    def boyant_exp(cls, name: str, max_val: u.Quantity, max_pressure: u.Quantity, pressure: Pressure):
        """
        Creates an Aerosol object with a concentration that floats at a certain pressure
        and falls off exponentially with height.

        Parameters
        ----------
        name : str
            The name of the aerosol variable.
        max_val : astropy.units.Quantity
            The maximum aerosol concentration value.
        max_pressure : astropy.units.Quantity
            The maximum pressure threshold above which the aerosol concentration is non-neglegable.
        pressure : Pressure
            The pressure profile of the planet.

        Returns
        -------
        Aerosol
            An Aerosol object with aerosol concentration values that fall off exponentially with height.
        """

        dat = np.where(pressure.dat > max_pressure, 1e-20 *
                       u.Unit('kg kg-1'), max_val * (pressure.dat/max_pressure))
        return cls(name, dat)


class AerosolSize(Variable3D):
    """
    A subclass of Variable representing aerosol particle sizes.

    Parameters
    ----------
    name : str
        The name of the aerosol size variable.
    dat : astropy.units.Quantity
        The aerosol particle sizes at every point.

    Attributes
    ----------
    name : str
        The name of the aerosol size variable.
    psg_unit : astropy.units.Unit
        The physical unit of the aerosol particle sizes, which is set to  Log[meters ('m')] using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the aerosol particle sizes as a `astropy.units.Quantity` object.

    """

    def __init__(self, name: str, dat: u.Quantity):
        super().__init__(name, u.LogUnit(u.m), dat)

    @classmethod
    def constant(cls, name: str, val: u.Quantity, shape: tuple):
        """
        Creates an AerosolSize object with constant aerosol particle sizes.

        Parameters
        ----------
        name : str
            The name of the aerosol size variable.
        val : astropy.units.Quantity
            The constant aerosol particle size value.
        shape : tuple
            The shape of the aerosol particle sizes data array.

        Returns
        -------
        AerosolSize
            An AerosolSize object with constant aerosol particle sizes specified by the given name, value, and shape.
        """

        dat = np.ones(shape=shape) * val
        return cls(name, dat)


class Albedo(Variable2D):
    """
    A subclass of Variable representing albedo values.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The albedo values at every point.

    Attributes
    ----------
    name : str
        The name of the albedo variable, set to 'Albedo'.
    psg_unit : astropy.units.Unit
        The physical unit of the albedo values, which is set to dimensionless using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the albedo variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, dat: u.Quantity):
        dat = u.Quantity(dat)
        super().__init__('Albedo', u.dimensionless_unscaled, dat)

    @classmethod
    def constant(cls, val: u.Quantity, shape: tuple):
        """
        Creates an Albedo object with constant albedo values.

        Parameters
        ----------
        val : astropy.units.Quantity
            The constant albedo value.
        shape : tuple
            The shape of the albedo data array.

        Returns
        -------
        Albedo
            An `Albedo` object with constant albedo values specified by the given value, and shape.
        """

        dat = np.ones(shape=shape) * val
        return cls(dat)


class Emissivity(Variable2D):
    """
    A subclass of Variable representing the emisivity of a planet.

    Parameters
    ----------
    dat : astropy.units.Quantity
        The emisivity values at every point.

    Attributes
    ----------
    name : str
        The name of the variable, set to 'Emissivity'.
    psg_unit : astropy.units.Unit
        The physical unit of the albedo values, which is set to dimensionless using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the albedo variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, dat: u.Quantity):
        super().__init__('Emissivity', u.dimensionless_unscaled, dat)

    @classmethod
    def constant(cls, val: u.Quantity, shape: tuple):
        """
        Creates an Emissivity object with constant emissivity values.

        Parameters
        ----------
        val : astropy.units.Quantity
            The constant albedo value.
        shape : tuple
            The shape of the albedo data array.

        Returns
        -------
        emissivity
            An `Emissivity` object with constant values specified by the given value, and shape.
        """

        dat = np.ones(shape=shape) * val
        return cls(dat)


class Surface(Variable2D):
    """
    A subclass of Variable representing the surface of a planet.

    Parameters
    ----------
    name : str
        The name of the surface variable.
    dat : astropy.units.Quantity
        The emisivity values at every point.

    Attributes
    ----------
    name : str
        The name of the albedo variable.
    psg_unit : astropy.units.Unit
        The physical unit of the surface values, which is set to dimensionless using the `astropy.units` module.
    dat : astropy.units.Quantity
        The data values of the albedo variable as a `astropy.units.Quantity` object.

    """

    def __init__(self, name: str, dat: u.Quantity):
        super().__init__(name, u.dimensionless_unscaled, dat)

    @classmethod
    def constant(cls, name: str, val: u.Quantity, shape: tuple):
        """
        Creates a Surface object with constant values.

        Parameters
        ----------
        val : astropy.units.Quantity
            The constant albedo value.
        shape : tuple
            The shape of the albedo data array.

        Returns
        -------
        dat : astropy.units.Quantity
            A `Surface` object with constant values specified by the given value, and shape.
        """

        dat = np.ones(shape=shape) * val
        return cls(name, dat)
