"""
Methods to parse config files.
"""
from typing import Union, Type
from pathlib import Path

import warnings

from pypsg.cfg import models

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
        if self.has_binary:
            content = content.split(b'<BINARY>')[0] + content.split(b'</BINARY>')[1]
        content = str(content,encoding=self.encoding)
        cfg = {}
        for line in content.split('\n'):
            if not (line.isspace() or len(line)==0):
                end_of_kwd = line.index('>')+1
                kwd = line[:end_of_kwd].replace('<','').replace('>','')
                val = line[end_of_kwd:]
                cfg[kwd] = val
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
        generator:models.Generator = None,
        telescope:models.Telescope = None,
        noise:models.Noise = None
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
            self.atmosphere = models.NoAtmosphere()
        
        self.generator:models.Generator = generator
        if self.generator is None:
            self.generator = models.Generator()
        
        self.telescope:Union[
            models.SingleTelescope,models.Interferometer,models.Coronagraph,
            models.AOTF,models.LIDAR
            ] = telescope
        if self.telescope is None:
            self.telescope = models.SingleTelescope()
        
        self.noise:Union[
            models.Noiseless,models.RecieverTemperatureNoise,
            models.ConstantNoise,models.ConstantNoiseWithBackground,
            models.PowerEquivalentNoise,models.Detectability,models.CCD
            ] = noise
        if self.noise is None:
            self.noise = models.Noiseless()
    @classmethod
    def from_dict(cls,d:dict):
        return cls(
            target=models.Target.from_cfg(d),
            geometry=models.Geometry.from_cfg(d),
            atmosphere=models.Atmosphere.from_cfg(d),
            generator=models.Generator.from_cfg(d),
            telescope=models.Telescope.from_cfg(d),
            noise=models.Noise.from_cfg(d)
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
        return b'\n'.join([
            self.target.content,
            self.geometry.content,
            self.atmosphere.content,
            self.generator.content,
            self.telescope.content,
            self.noise.content
        ])