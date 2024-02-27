"""
Methods to parse config files.
"""
from typing import Union, Dict, Any
from pathlib import Path

import warnings

from pypsg.cfg import models
from pypsg import settings
from pypsg.globes import PyGCM


class ConfigTooLongWarning(UserWarning):
    """
    The PSG configuration is too long,
    and may stop updating soon.
    """


class BinConfig:
    """
    PSG configuration structure.

    Parameters
    ----------
    content : bytes
        The content of the configuration.

    Attributes
    ----------
    enconding : str
        The encoding of the config. Set to 'UTF-8'.
    content : bytes
        The content of the config.
    has_binary : bool
        True if there is a `<BINARY>` section in the config.
    """
    encoding = 'UTF-8'

    def __init__(self, content: bytes):
        self.content = content

    @classmethod
    def from_file(cls, path: Path):
        """
        Read a config from a file.

        Parameters
        ----------
        path : pathlib.Path
            The path to the file.

        Returns
        -------
        Config
            A config constructed using the provided file.
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        with open(path, 'rb') as file:
            content = file.read()
        return cls(content=content)

    @property
    def has_binary(self) -> bool:
        """
        True if the config contains a binary section

        :type: bool
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        return b'<BINARY>' in self.content

    @property
    def binary(self) -> bytes:
        """
        The binary section of the config.

        :type: bytes
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        if not self.has_binary:
            raise ValueError('This config contains no binary section.')
        return self.content.split(b'<BINARY>')[1].split(b'</BINARY>')[0]

    @property
    def dict(self) -> dict:
        """
        A dictionary with all the keyword, value pairs.

        :type: dict
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        content = self.content
        binary = None
        if self.has_binary:
            content = content.split(b'<BINARY>')[
                0] + content.split(b'</BINARY>')[1]
            binary = self.binary
        content = str(content, encoding=self.encoding)
        n_lines = len(content.split('\n'))
        if n_lines > settings.get_setting('cfg_max_lines'):
            warnings.warn('The config is too long.', ConfigTooLongWarning)
        cfg = {}
        for line in content.split('\n'):
            if not (line.isspace() or len(line) == 0 or line[0] == '#'):
                try:
                    end_of_kwd = line.index('>')+1
                except ValueError as err:
                    raise ValueError(f'Invalid config line: {line}') from err
                kwd = line[:end_of_kwd].replace('<', '').replace('>', '')
                val = line[end_of_kwd:]
                cfg[kwd] = val
        if binary is not None:
            cfg['BINARY'] = binary
        return cfg


class PyConfig:
    """
    A configuration in the form of a python object.

    Parameters
    ----------
    target : models.Target, optional
        Target model, by default None
    geometry : models.Geometry, optional
        Geometry model, by default None
    atmosphere : models.Atmosphere, optional
        Atmosphere model, by default None
    surface : models.Surface, optional
        Surface model, by default None
    generator : models.Generator, optional
        Generator model, by default None
    telescope : models.Telescope, optional
        Telescope model, by default None
    noise : models.Noise, optional
        Noise model, by default None
    gcm : globes.PyGCM, optional
        GCM model, by default None
    """

    def __init__(
        self,
        target: models.Target = None,
        geometry: models.Geometry = None,
        atmosphere: models.Atmosphere = None,
        surface: models.Surface = None,
        generator: models.Generator = None,
        telescope: models.Telescope = None,
        noise: models.Noise = None,
        gcm: PyGCM = None
    ):
        self.target: models.Target = target
        if self.target is None:
            self.target = models.Target()

        self.geometry: models.Geometry = geometry
        if self.geometry is None:
            self.geometry = models.Geometry()

        self.atmosphere: Union[
            models.NoAtmosphere, models.EquilibriumAtmosphere, models.ComaAtmosphere
        ] = atmosphere
        if self.atmosphere is None:
            self.atmosphere = models.Atmosphere()

        self.surface: models.Surface = surface
        if self.surface is None:
            self.surface = models.Surface()

        self.generator: models.Generator = generator
        if self.generator is None:
            self.generator = models.Generator()

        self.telescope: Union[
            models.SingleTelescope, models.Interferometer, models.Coronagraph,
            models.AOTF, models.LIDAR
        ] = telescope
        if self.telescope is None:
            self.telescope = models.Telescope()

        self.noise: Union[
            models.Noiseless, models.RecieverTemperatureNoise,
            models.ConstantNoise, models.ConstantNoiseWithBackground,
            models.PowerEquivalentNoise, models.Detectability, models.CCD
        ] = noise
        if self.noise is None:
            self.noise = models.Noise()

        self.gcm: PyGCM | None = gcm

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        """
        Construct a PyConfig from a dictionary.

        Parameters
        ----------
        d : dict
            A dictionary representation of a PSG config file,
            in the format `{'OBJECT-NAME':'Earth'}`. Note that the
            keys must all be captial letters.

        Notes
        -----
        * Missing keys, provided they are all uppercase, are ignored.
        * Some fields require more than one key. In the case that only one
          is provided, it will be ignored.
        * The actual parsing of the dictionary is done by each field.
        """
        for key in d:
            if not key.isupper():
                raise ValueError(f'Invalid config key: {key}')
        has_gcm = 'ATMOSPHERE-GCM-PARAMETERS' in d and 'BINARY' in d
        gcm = PyGCM.from_cfg(d) if has_gcm else None
        atmosphere = models.Atmosphere.from_cfg(d)
        if has_gcm and isinstance(atmosphere, models.EquilibriumAtmosphere):
            atmosphere = gcm.update_params(atmosphere)

        return cls(
            target=models.Target.from_cfg(d),
            geometry=models.Geometry.from_cfg(d),
            atmosphere=atmosphere,
            surface=models.Surface.from_cfg(d),
            generator=models.Generator.from_cfg(d),
            telescope=models.Telescope.from_cfg(d),
            noise=models.Noise.from_cfg(d),
            gcm=gcm
        )

    @classmethod
    def from_binaryconfig(cls, config: BinConfig):
        """
        Construct a PyConfig from a BinConfig object.

        Parameters
        ----------
        config : BinConfig
            A BinConfig object.
        """
        return cls.from_dict(config.dict)

    @classmethod
    def from_bytes(cls, config: bytes):
        """
        Construct a PyConfig from bytes.

        Parameters
        ----------
        config : bytes
            The bytes representation of a config file.
        """
        return cls.from_binaryconfig(BinConfig(config))

    @classmethod
    def from_file(cls, path: Path | str):
        """
        Construct a PyConfig from a file.

        Parameters
        ----------
        path : pathlib.Path | str
            The path to the file.
        """
        return cls.from_binaryconfig(BinConfig.from_file(path))

    @property
    def content(self) -> bytes:
        """
        Get the config content as a bytes string.
        """
        lines = []
        for model in [
            self.target,
            self.geometry,
            self.gcm.update_params(self.atmosphere) if self.gcm is not None else self.atmosphere,
            self.surface,
            self.generator,
            self.telescope,
            self.noise
        ]:
            model: models.Model
            c = model.content
            if c != b'':
                lines.append(c)
        if self.gcm is not None:
            lines.append(self.gcm.content)
        return b'\n'.join(lines)

    def to_file(self, path: Path | str):
        """
        Write the config to a file.

        Parameters
        ----------
        path : pathlib.Path | str
            The path to the file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(self.content)
