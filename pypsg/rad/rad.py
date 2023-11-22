"""
Python representation of rad files.
"""

from pathlib import Path
import re
import numpy as np

from specutils import Spectrum1D
import astropy.units as u

from pypsg import settings



class BinRad:
    """
    Binary representation of rad files.
    """
    def __init__(self,content:bytes):
        self.content = content
    @classmethod
    def from_file(cls,path:Path):
        with open(path,'rb') as file:
            content = file.read()
        return cls(content=content)


class PyRad:
    """
    Python representation of rad files.
    """
    def __init__(
        self,
        total:Spectrum1D,
        noise:Spectrum1D=None,
        star:Spectrum1D=None,
        target:Spectrum1D=None,
        thermal:Spectrum1D=None,
        reflected:Spectrum1D=None
    ):
        self.total = total
        self.noise = noise
        self.star = star
        self.target = target
        self.thermal = thermal
        self.reflected = reflected
    @classmethod
    def from_bytes(cls,b:bytes):
        lines = b.split(b'\n')
        header = [line.decode(settings.get_setting('encoding')) for line in lines if line.startswith(b'#')]
        content = [line.decode(settings.get_setting('encoding')) for line in lines if (not line.startswith(b'#') and len(line)>0)]
        names = header[-1].split(' ')[1:]
        radiance_unit_line = header[-2]
        radiance_unit = u.Unit(
            re.findall(r'\[([\w\d/]+)\]', radiance_unit_line)[0].replace('W/m2/um','W m-2 um-1')
        )
        spectral_unit_line = header[-3]
        spectral_unit = u.Unit(
            re.findall(r'\[([\w\d/]+)\]', spectral_unit_line)[0]
        )
        content = np.array(
            [
                np.fromstring(line,sep=' ') for line in content
            ]
        )
        spectra = {
            name:content[:,i] for i,name in enumerate(names)
        }
        wl = spectra['Wave/freq'] * spectral_unit
        name_mapping = {
            'Total': 'total',
            'Noise': 'noise',
            'Stellar': 'star',
            'Thermal': 'thermal',
            'Reflected': 'reflected'
        }
        kwargs = {}
        for name in names:
            if name != 'Wave/freq':
                dat = spectra[name]*radiance_unit
                kwargs[name_mapping.get(name,'target')] = Spectrum1D(
                    spectral_axis=wl,flux=dat
                )
        return cls(**kwargs)
        
        
        
        
        