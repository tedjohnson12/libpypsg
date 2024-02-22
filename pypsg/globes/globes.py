"""
Handling of PSG's Global Emission Spectra (GlobES) application
"""
from typing import Any, Tuple, List
import numpy as np
from astropy import units as u, constants as c

from . import structure
from ..cfg.models import EquilibriumAtmosphere
from ..cfg.base import Molecule, Aerosol, Profile
from ..settings import atmosphere_type_dict as mtype, aerosol_type_dict as atype, get_setting
from .decoder import GCMdecoder, sep_header

ANGLE_UNIT = u.deg
DTYPE = np.float32


class GCM:
    """
    Global Circulation Model (GCM)

    Parameters
    ----------
    header : str
        The header of the GCM. This tells PSG how to interpret the data.
    dat : np.ndarray
        The data of the GCM.
    """
    KEY = 'ATMOSPHERE-GCM-PARAMETERS'
    BIN_KEY = 'BINARY'
    ENCODING = 'UTF-8'

    def __init__(
        self,
        header: str,
        dat: np.ndarray
    ):
        self.header = header
        self.dat = dat

    @classmethod
    def from_cfg(cls, d: dict):
        """
        Read a GCM from a config dict.

        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        """
        if cls.KEY not in d:
            return None
        if cls.BIN_KEY not in d:
            return None
        header = d[cls.KEY]
        bin_dat: bytes = d[cls.BIN_KEY]
        dat = np.frombuffer(bin_dat, dtype=np.float32)
        return cls(header, dat)

    @property
    def content(self) -> bytes:
        """
        Get the content of the GCM in a format that PSG can read.

        Returns
        -------
        bytes
            The content of the GCM.
        """
        params_line = bytes(
            f'<{self.KEY}>{self.header}\n', encoding=self.ENCODING)
        start_tag = bytes(f'<{self.BIN_KEY}>', encoding=self.ENCODING)
        end_tag = bytes(f'</{self.BIN_KEY}>', encoding=self.ENCODING)
        dat = self.dat.tobytes(order='C')
        return params_line + b'\n' + start_tag + dat + end_tag


class PyGCM:
    """
    A Python container for GCM data.

    Parameters
    ----------
    pressure : pypsg.globes.structure.Pressure
        The pressure variable.
    temperature : pypsg.globes.structure.Temperature
        The temperature variable.
    wind_u : pypsg.globes.structure.Wind, optional
        The west-to-east wind variable.
    wind_v : pypsg.globes.structure.Wind, optional
        The south-to-north wind variable.
    tsurf : pypsg.globes.structure.SurfaceTemperature, optional
        The surface temperature variable.
    psurf : pypsg.globes.structure.SurfacePressure, optional
        The surface pressure variable.
    albedo : pypsg.globes.structure.Albedo, optional
        The albedo variable.
    emissivity : pypsg.globes.structure.Emissivity, optional
        The emissivity variable.
    *args : pypsg.globes.structure.Molecule | pypsg.globes.structure.Aerosol | pypsg.globes.structure.AerosolSize | pypsg.globes.structure.Surface
        Additional variables.
    """
    _key_order = [
        'wind_u',
        'wind_v',
        'pressure',
        'temperature',
        'tsurf',
        'psurf',
        'albedo',
        'emissivity'
    ]

    def __init__(
        self,
        pressure: structure.Pressure,
        temperature: structure.Temperature,
        *args: structure.Molecule | structure.Aerosol | structure.AerosolSize | structure.Surface,
        wind_u: structure.Wind = None,
        wind_v: structure.Wind = None,
        tsurf: structure.SurfaceTemperature = None,
        psurf: structure.SurfacePressure = None,
        albedo: structure.Albedo = None,
        emissivity: structure.Emissivity = None,
        lon_start: float = -180.,
        lat_start: float = -90.,
        desc: str = None,
    ):
        self.pressure = pressure
        self.temperature = temperature
        self.wind_u = structure.Wind.zero(
            'wind_u', pressure.shape) if wind_u is None else wind_u
        self.wind_v = structure.Wind.zero(
            'wind_v', pressure.shape) if wind_v is None else wind_v
        self.tsurf = tsurf
        self.psurf = psurf
        self.albedo = albedo
        self.emissivity = emissivity
        for arg in args:
            self.__setattr__(arg.name, arg)
        self.lon_start = lon_start
        self.lat_start = lat_start
        self.desc = desc
        self.variables = self._variables

    def __setattr__(self, __name: str, __value: Any) -> None:
        """
        Enforce shapes match pressure data.
        """
        if __name == 'pressure':  # must be set first
            pass
        else:
            nlayers, nlon, nlat = self.shape
            if __value is None:
                pass
            elif isinstance(__value, structure.Variable3D):
                if __value.shape != (nlayers, nlon, nlat):
                    raise ValueError(
                        f'Dimension mismatch: {__value.shape} != ({nlayers},{nlon},{nlat})')
            elif isinstance(__value, structure.Variable2D):
                if __value.shape != (nlon, nlat):
                    raise ValueError(
                        f'Dimension mismatch: {__value.shape} != ({nlon},{nlat})')

        super().__setattr__(__name, __value)

    @property
    def shape(self) -> Tuple[int, int, int]:
        """
        Get the shape of the data.

        Returns
        -------
        nlayers : int
            The number of layers.
        nlon : int
            The number of longitudes.
        nlat : int
            The number of latitudes.
        """
        nlayers, nlon, lat = self.pressure.shape
        return nlayers, nlon, lat

    @property
    def _variables(self) -> List[structure.Variable]:
        """
        Enforce variable order is consistent across outputs.
        """
        variables = []
        for key in self._key_order:
            value = self.__getattribute__(key)
            if value is not None:
                variables.append(value)
        for key, value in self.__dict__.items():
            if key not in self._key_order and isinstance(value, structure.Variable):
                variables.append(value)
        return variables

    @property
    def dlon(self) -> u.Quantity:
        """
        Returns the longitudinal grid spacing.

        Returns
        -------
        dlon : u.Quantity
            The longitudinal grid spacing.
        """

        _, nlon, _ = self.shape
        return 360*u.deg / (nlon)

    @property
    def dlat(self) -> u.Quantity:
        """
        Returns the latitudinal grid spacing.

        Returns
        -------
        dlat : u.Quantity
            The latitudinal grid spacing.
        """

        _, _, nlat = self.shape
        return 180*u.deg / (nlat)

    @property
    def lons(self) -> np.ndarray:
        """
        Get the longitude values.
        """
        _, nlon, _ = self.shape
        return self.lon_start + np.arange(nlon+1) * self.dlon.to_value(ANGLE_UNIT)

    @property
    def lats(self) -> np.ndarray:
        """
        Get the latitude values.
        """
        _, _, nlat = self.shape
        return self.lat_start + np.arange(nlat+1) * self.dlat.to_value(ANGLE_UNIT)

    @property
    def header(self):
        """
        Constructs the string value of the PSG ``<ATMOSPHERE-GCM-PROPERTIES>`` parameter.

        Returns
        -------
        header : str
            The header of the GCM.
        """
        nlayer, nlon, nlat = self.shape
        coords = f'{nlon},{nlat},{nlayer},{self.lon_start:.1f},{self.lat_start:.1f},{self.dlon.to_value(ANGLE_UNIT):.2f},{self.dlat.to_value(ANGLE_UNIT):.2f}'
        variables = self.variables[2:]  # Skip both winds.
        var_names = ['Winds'] + [v.name for v in variables]
        return f'{coords},{",".join(var_names)}'

    @property
    def flat(self) -> np.ndarray:
        """
        A flat array with all the data layed out as expected.

        Returns
        -------
        np.ndarray
            The flattened array.
        """
        return np.concatenate([v.flat.astype(DTYPE) for v in self.variables]).astype(DTYPE)

    @property
    def molecules(self):
        """
        Get the molecules.
        """
        return [molecule for molecule in self.__dict__.values() if isinstance(molecule, structure.Molecule)]

    @property
    def aerosols(self):
        """
        Get the aerosols.
        """
        return [aerosol for aerosol in self.__dict__.values() if isinstance(aerosol, structure.Aerosol)]

    @property
    def aerosol_sizes(self):
        """
        Get the aerosol sizes.
        """
        return [aerosol_size for aerosol_size in self.__dict__.values() if isinstance(aerosol_size, structure.AerosolSize)]

    def update_params(self, atmosphere: EquilibriumAtmosphere = None):
        """
        Update the config.
        """
        if not isinstance(atmosphere, EquilibriumAtmosphere):
            atmosphere = EquilibriumAtmosphere()

        gases = [molec.name for molec in self.molecules]
        aeros = [aerosol.name for aerosol in self.aerosols]
        gas_types = [f'HIT[{mtype[gas]}]' if isinstance(
            mtype[gas], int) else mtype[gas] for gas in gases]
        aerosol_types = [atype[aerosol] for aerosol in aeros]

        molecules = [Molecule(gas, gas_type, 1)
                     for gas, gas_type in zip(gases, gas_types)]
        aerosols = [Aerosol(aerosol, aerosol_type, 1, 1)
                    for aerosol, aerosol_type in zip(aeros, aerosol_types)]
        
        pressure_dat = self.pressure.dat[:, 0, 0].to_value(self.pressure.psg_unit)
        temperature_dat = self.temperature.dat[:, 0, 0].to_value(self.temperature.psg_unit)
        pressure = Profile('Pressure', pressure_dat, u.bar)
        temperature = Profile('Temperature', temperature_dat, u.K)
        

        atmosphere.description = self.desc
        atmosphere.molecules = tuple(molecules) if len(molecules) > 0 else None
        atmosphere.aerosols = tuple(aerosols) if len(aerosols) > 0 else None
        atmosphere.profile = tuple([pressure, temperature])
        return atmosphere

    @classmethod
    def from_decoder(cls, decoder: GCMdecoder):
        """
        Read a GCM from a decoder.
        """
        coords, variables = sep_header(decoder.header)
        pressure = decoder['Pressure']
        pressure = structure.Pressure(10**pressure * u.bar)
        temperature = decoder['Temperature']
        temperature = structure.Temperature(temperature * u.K)            
        
        args = {}
        
        molecules = decoder.get_molecules()
        for molecule in molecules:
            args[molecule] = structure.Molecule(molecule, (10**decoder[molecule])*u.dimensionless_unscaled)
        aerosols, aerosol_sizes = decoder.get_aerosols()
        for aerosol, aerosol_size in zip(aerosols, aerosol_sizes):
            args[aerosol] = structure.Aerosol(aerosol, (10**decoder[aerosol])*u.dimensionless_unscaled)
            args[aerosol_size] = structure.AerosolSize(
                aerosol_size, 10**(decoder[aerosol_size])*u.m)
        
        kwargs = {}
        if 'Wind' in variables:
            wind = decoder['Wind']
            wind_u = wind[0, :, :, :] * u.m / u.s
            wind_v = wind[1, :, :, :] * u.m / u.s
            kwargs['wind_u'] = structure.Wind('wind_u', wind_u)
            kwargs['wind_v'] = structure.Wind('wind_v', wind_v)
        if 'Tsurf' in variables:
            tsurf = decoder['Tsurf']
            kwargs['tsurf'] = structure.SurfaceTemperature(tsurf * u.K)
        if 'Psurf' in variables:
            psurf = decoder['Psurf']
            kwargs['psurf'] = structure.SurfacePressure(10**psurf * u.bar)
        if 'Albedo' in variables:
            albedo = decoder['Albedo']
            kwargs['albedo'] = structure.Albedo(albedo*u.dimensionless_unscaled)
        if 'Emissivity' in variables:
            emissivity = decoder['Emissivity']
            kwargs['emissivity'] = structure.Emissivity(emissivity*u.dimensionless_unscaled)

        _, _, _, lon_start, lat_start, _, _ = coords
        kwargs['lon_start'] = float(lon_start)
        kwargs['lat_start'] = float(lat_start)

        return cls(pressure,temperature, *args.values(), **kwargs)

    @classmethod
    def from_bytes(cls, header: str, binary: bytes):
        """
        Read a GCM from bytes.

        Parameters
        ----------
        header : str
            The header of the GCM.
        binary : bytes
            The binary data of the GCM.
        """
        decoder = GCMdecoder(header, np.frombuffer(binary,dtype='float32'))
        return cls.from_decoder(decoder)

    @classmethod
    def from_cfg(cls, d: dict):
        """
        Read a GCM from a config dict.

        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        """
        header = d['ATMOSPHERE-GCM-PARAMETERS']
        dat = d['BINARY']
        return cls.from_bytes(header, dat)

    @property
    def content(self)-> bytes:
        """
        Get the content of the GCM in a format that PSG can read.

        Returns
        -------
        bytes
            The content of the GCM.
        """
        gcm_params = b'<ATMOSPHERE-GCM-PARAMETERS>' + self.header.encode(get_setting('encoding'))
        binary = b'<BINARY>' + self.flat.tobytes(order='C') + b'</BINARY>'
        return gcm_params + b'\n' + binary
    
    def altitude(self, mass: u.Quantity, radius: u.Quantity, mean_molecular_mass: float) -> u.Quantity:
        """
        Use the equation of hydrostatic equilibrium to calculate the
        altitude of each grid point.

        Parameters
        ----------
        mass : u.Quantity
            The mass of the planet.
        radius : u.Quantity
            The radius of the planet's surface (the bottom layer).
        mean_molecular_mass : float
            The mean molecular mass of the atmosphere.

        Returns
        -------
        z : u.Quantity
            The altitude of each grid point.
        """
        pressure = self.pressure
        temperature = self.temperature
        nlayer, nlon, nlat = self.shape
        z_unit = u.km
        z = np.zeros(shape=(nlayer, nlon, nlat))
        for i in range(nlayer-1):
            pressure_bottom = pressure.dat[i, :, :].to(u.bar)
            pressure_top = pressure.dat[i+1, :, :].to(u.bar)
            dP = pressure_top - pressure_bottom
            # pylint: disable-next=no-member
            rho = mean_molecular_mass*u.Unit('g mol-1') * \
                (pressure_bottom + 0.5*dP) / c.R / temperature.dat[i, :, :]
            distance_from_planet_center = radius + z[i, :, :]*z_unit
            # pylint: disable-next=no-member
            accel_due_to_gravity = c.G * mass / distance_from_planet_center**2
            dz = -dP / rho / accel_due_to_gravity
            z[i+1, :, :] = z[i, :, :] + dz.to_value(z_unit)
        return z*z_unit

    @staticmethod
    def _column_gas(
        molecule: structure.Molecule,
        pressure: u.Quantity,
        temperature: u.Quantity,
        altitude: u.Quantity
    ) -> u.Quantity:
        """
        Get the column density of a gas.

        Parameters
        ----------
        molecule : structure.Molecule
            The molecule to get the column density of.
        pressure : u.Quantity
            The pressure at each grid point.
        temperature : u.Quantity
            The temperature at each grid point.
        altitude : u.Quantity
            The altitude at each grid point.

        Returns
        -------
        u.Quantity
            The column density of the gas.
        """
        abundance = molecule.dat.to(u.dimensionless_unscaled)
        partial_pressure = pressure * abundance
        heights = np.diff(altitude, axis=0)
        # pylint: disable-next=no-member
        surface_density: u.Quantity = partial_pressure[:-
                                                       1] * heights / c.R / temperature[:-1]
        return surface_density.sum(axis=0).to(u.mol/u.cm**2)

    @staticmethod
    def _column_aerosol(
        aerosol: structure.Aerosol,
        pressure: u.Quantity,
        temperature: u.Quantity,
        altitude: u.Quantity,
        mean_molecular_mass: float
    ):
        """
        Get the column density of an aerosol.

        Parameters
        ----------
        aerosol : structure.Aerosol
            The aerosol to get the column density of.
        pressure : u.Quantity
            The pressure at each grid point.
        temperature : u.Quantity
            The temperature at each grid point.
        altitude : u.Quantity
            The altitude at each grid point.
        mean_molecular_mass : float
            The mean molecular mass of the atmosphere.

        Returns
        -------
        u.Quantity
            The column density of the aerosol.
        """
        mass_frac = aerosol.dat.to_value(u.dimensionless_unscaled)[:-1,:,:]
        heights = np.diff(altitude, axis=0)
        mean_molecular_mass = mean_molecular_mass * u.g/u.mol
        # pylint: disable-next=no-member
        moles_of_gas_per_cm2 = pressure[:-1]*heights / c.R / temperature[:-1]
        mass_of_gas_per_cm2 = moles_of_gas_per_cm2 * mean_molecular_mass
        mass_of_aero_per_cm2 = mass_of_gas_per_cm2 * mass_frac
        return mass_of_aero_per_cm2.sum(axis=0).to(u.kg/u.cm**2)

    def column(
        self,
        var: str,
        mass: u.Quantity,
        radius: u.Quantity,
        mean_molecular_mass: float
    ):
        """
        Get a 2D column density map of a GCM variable.

        Parameters
        ----------
        var : str
            The name of the variable to get the column density of.
        mass : u.Quantity
            The mass of the planet.
        radius : u.Quantity
            The radius of the planet.
        mean_molecular_mass : float
            The mean molecular mass of the atmosphere.

        Returns
        -------
        u.Quantity
            The column density of the variable. The unit depends on the type of variable.
        """
        variable = self.__getattribute__(var)
        if not isinstance(variable, structure.Variable3D):
            raise ValueError(f'{var} is not a 3D variable.')

        pressure = self.pressure.dat.to(u.bar)
        altitude = self.altitude(mass, radius, mean_molecular_mass)
        temperature = self.temperature.dat.to(u.K)
        if isinstance(variable, structure.Molecule):
            return self._column_gas(variable, pressure, temperature, altitude)
        elif isinstance(variable, structure.Aerosol):
            return self._column_aerosol(variable, pressure, temperature, altitude, mean_molecular_mass)
        else:
            raise ValueError(f'{var} is not a molecule or aerosol.')
