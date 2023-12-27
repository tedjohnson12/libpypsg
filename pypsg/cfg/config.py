"""
Methods to parse config files.
"""
from typing import Union, Type
from pathlib import Path

import warnings

from pypsg.cfg import models, globes
from pypsg import settings


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
    encoding='UTF-8'
    def __init__(self,content:bytes):
        self.content = content
    @classmethod
    def from_file(cls,path:Path):
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
        with open(path,'rb') as file:
            content = file.read()
        return cls(content=content)
    @property
    def has_binary(self)->bool:
        """
        True if the config contains a binary section
        
        :type: bool
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        return b'<BINARY>' in self.content
    @property
    def binary(self)->bytes:
        """
        The binary section of the config.
        
        :type: bytes
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        if not self.has_binary:
            raise ValueError('This config contains no binary section.')
        return self.content.split(b'<BINARY>')[1].split(b'</BINARY>')[0]
    @property
    def dict(self)->dict:
        """
        A dictionary with all the keyword, value pairs.

        :type: dict
        """
        # warnings.warn('This method has not been tested.',RuntimeWarning)
        content = self.content
        binary = None
        if self.has_binary:
            content = content.split(b'<BINARY>')[0] + content.split(b'</BINARY>')[1]
            binary = self.binary
        content = str(content,encoding=self.encoding)
        n_lines = len(content.split('\n'))
        if n_lines > settings.get_setting('cfg_max_lines'):
            warnings.warn('The config is too long.',ConfigTooLongWarning)
        cfg = {}
        for line in content.split('\n'):
            if not (line.isspace() or len(line)==0):
                end_of_kwd = line.index('>')+1
                kwd = line[:end_of_kwd].replace('<','').replace('>','')
                val = line[end_of_kwd:]
                cfg[kwd] = val
        if binary is not None:
            cfg['BINARY'] = binary
        return cfg

class PyConfig:
    """
    A configuration in the form of a python object.
    """
    def __init__(
        self,
        target:models.Target = None,
        geometry:models.Geometry = None,
        atmosphere:models.Atmosphere = None,
        surface:models.Surface = None,
        generator:models.Generator = None,
        telescope:models.Telescope = None,
        noise:models.Noise = None,
        gcm:globes.GCM = None
    ):
        self.target:models.Target = target
        if self.target is None:
            self.target = models.Target()
        
        self.geometry:models.Geometry = geometry
        if self.geometry is None:
            self.geometry = models.Geometry()
        
        self.atmosphere:Union[
            models.NoAtmosphere,models.EquilibriumAtmosphere,models.ComaAtmosphere
            ] = atmosphere
        if self.atmosphere is None:
            self.atmosphere = models.Atmosphere()
        
        self.surface:models.Surface = surface
        if self.surface is None:
            self.surface = models.Surface()
        
        self.generator:models.Generator = generator
        if self.generator is None:
            self.generator = models.Generator()
        
        self.telescope:Union[
            models.SingleTelescope,models.Interferometer,models.Coronagraph,
            models.AOTF,models.LIDAR
            ] = telescope
        if self.telescope is None:
            self.telescope = models.Telescope()
        
        self.noise:Union[
            models.Noiseless,models.RecieverTemperatureNoise,
            models.ConstantNoise,models.ConstantNoiseWithBackground,
            models.PowerEquivalentNoise,models.Detectability,models.CCD
            ] = noise
        if self.noise is None:
            self.noise = models.Noise()
        
        self.gcm:globes.GCM | None = gcm
        
    @classmethod
    def from_dict(cls,d:dict):
        return cls(
            target=models.Target.from_cfg(d),
            geometry=models.Geometry.from_cfg(d),
            atmosphere=models.Atmosphere.from_cfg(d),
            surface=models.Surface.from_cfg(d),
            generator=models.Generator.from_cfg(d),
            telescope=models.Telescope.from_cfg(d),
            noise=models.Noise.from_cfg(d),
            gcm=globes.GCM.from_cfg(d)
        )
    @classmethod
    def from_binaryconfig(cls,config:BinConfig):
        return cls.from_dict(config.dict)
    @classmethod
    def from_bytes(cls,config:bytes):
        return cls.from_binaryconfig(BinConfig(config))
    @classmethod
    def from_file(cls,path:Path):
        return cls.from_binaryconfig(BinConfig.from_file(path))
    @property
    def content(self)->bytes:
        lines = []
        for model in [
            self.target,
            self.geometry,
            self.atmosphere,
            self.surface,
            self.generator,
            self.telescope,
            self.noise
        ]:
            c = model.content
            if c != b'':
                lines.append(c)
        if self.gcm is not None:
            lines.append(self.gcm.content)
        return b'\n'.join(lines)
    def to_file(self,path:Path):
        """
        Write the config to a file.
        
        Parameters
        ----------
        path : pathlib.Path
            The path to the file.
        """
        with open(path,'wb') as f:
            f.write(self.content)