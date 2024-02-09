"""
Handling of PSG's Global Emission Spectra (GlobES) application
"""
from typing import Any, Tuple, List
import numpy as np
from astropy import units as u

from . import structure
from ..cfg.models import EquilibriumAtmosphere
from ..cfg.base import Molecule, Aerosol
from ..settings import atmosphere_type_dict as mtype, aerosol_type_dict as atype
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
    wind_u : pypsg.globes.structure.Wind, optional
        The west-to-east wind variable.
    wind_v : pypsg.globes.structure.Wind, optional
        The south-to-north wind variable.
    temperature : pypsg.globes.structure.Temperature, optional
        The temperature variable.
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
        *args: structure.Molecule | structure.Aerosol | structure.AerosolSize | structure.Surface,
        wind_u: structure.Wind = None,
        wind_v: structure.Wind = None,
        temperature: structure.Temperature = None,
        tsurf: structure.SurfaceTemperature = None,
        psurf: structure.SurfacePressure = None,
        albedo: structure.Albedo = None,
        emissivity: structure.Emissivity = None,
        lon_start: float = -180.,
        lat_start: float = -90.,
        desc: str = None,
    ):
        self.pressure = pressure
        self.wind_u = structure.Wind.zero(
            'wind_u', pressure.shape) if wind_u is None else wind_u
        self.wind_v = structure.Wind.zero(
            'wind_v', pressure.shape) if wind_v is None else wind_v
        self.temperature = temperature
        self.tsurf = tsurf
        self.psurf = psurf
        self.albedo = albedo
        self.emissivity = emissivity
        for arg in args:
            self.__setattr__(arg.name, arg)
        self.lon_start = lon_start
        self.lat_start = lat_start
        self.desc = desc

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
        return 360*u.deg / nlon

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
        return 180*u.deg / nlat
    @property
    def lons(self)-> u.Quantity:
        """
        Get the longitude values.
        """
        _, nlon, _ = self.shape
        return self.lon_start*u.deg + np.arange(nlon) * self.dlon
    
    @property
    def lats(self)-> u.Quantity:
        """
        Get the latitude values.
        """
        _, _, nlat = self.shape
        return self.lat_start*u.deg + np.arange(nlat) * self.dlat

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
        variables = self._variables[2:]  # Skip both winds.
        var_names = ['Wind'] + [v.name for v in variables]
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
        return np.concatenate([v.flat.astype(DTYPE) for v in self._variables])

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
        if atmosphere is None:
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

        atmosphere.description = self.desc
        atmosphere.molecules = tuple(molecules)
        atmosphere.aerosols = tuple(aerosols)
        atmosphere.profile = None
        return atmosphere

    @classmethod
    def from_decoder(cls, decoder: GCMdecoder):
        """
        Read a GCM from a decoder.
        """
        coords, variables = sep_header(decoder.header)
        kwargs = {}
        if 'Wind' in variables:
            wind = decoder['Wind']
            wind_u = wind[0, :, :, :] * u.m / u.s
            wind_v = wind[1, :, :, :] * u.m / u.s
            kwargs['wind_u'] = structure.Wind('wind_u', wind_u)
            kwargs['wind_v'] = structure.Wind('wind_v', wind_v)
        if 'Pressure' in variables:
            pressure = decoder['Pressure']
            kwargs['pressure'] = structure.Pressure(10**pressure * u.bar)
        if 'Temperature' in variables:
            temperature = decoder['Temperature']
            kwargs['temperature'] = structure.Temperature(temperature * u.K)
        if 'Tsurf' in variables:
            tsurf = decoder['Tsurf']
            kwargs['tsurf'] = structure.SurfaceTemperature(tsurf * u.K)
        if 'Psurf' in variables:
            psurf = decoder['Psurf']
            kwargs['psurf'] = structure.SurfacePressure(10**psurf * u.bar)
        if 'Albedo' in variables:
            albedo = decoder['Albedo']
            kwargs['albedo'] = structure.Albedo(albedo)
        if 'Emissivity' in variables:
            emissivity = decoder['Emissivity']
            kwargs['emissivity'] = structure.Emissivity(emissivity)

        molecules = decoder.get_molecules()
        for molecule in molecules:
            kwargs[molecule] = structure.Molecule(molecule, decoder[molecule])
        aerosols, aerosol_sizes = decoder.get_aerosols()
        for aerosol, aerosol_size in zip(aerosols, aerosol_sizes):
            kwargs[aerosol] = structure.Aerosol(aerosol, decoder[aerosol])
            kwargs[aerosol_size] = structure.AerosolSize(
                aerosol_size, decoder[aerosol_size]*u.m)

        _, _, _, lon_start, lat_start, _, _ = coords
        kwargs['lon_start'] = lon_start
        kwargs['lat_start'] = lat_start

        return cls(**kwargs)

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
        decoder = GCMdecoder(header, binary)
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
