"""
Python representation of rad files.
"""

from pathlib import Path
import re
import numpy as np

import astropy.units as u
from astropy import table

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


class PyRad(table.QTable):
    """
    Python representation of rad files.
    """
    SPEC_UNIT = 'SPECUNIT'
    RAD_UNIT = 'RADUNIT'
    _NAMES = 'NAMES'
    @staticmethod
    def _get_metadata(header:str):
        metadata = {}
        
        # metadata['type'] = re.findall(
        #     r'#[ ]+([\w]+ spectrum)',
        #     header
        # )[0]
        # metadata['source'] = re.findall(
        #     r'spectrum\n#(.+)\n',
        #     header
        # )[0]
        # metadata['date'] = re.findall(
        #     r'# Synthesized on (.+)\n',
        #     header
        # )[0]
        
        # vel_unit = u.Unit(
        #     re.findall(r'Doppler velocities \[(.+)\] ',header)[0]
        # )
        # vel_names = re.findall(
        #     r'Doppler velocities \[.+\] \((.+)\)',
        #     header
        # )[0].split(',')
        # vel_values = re.findall(
        #     r'Doppler velocities.+:(.+)\n',
        #     header
        # )[0].split(',')
        # for name,value in zip(vel_names,vel_values):
        #     metadata[name] = float(value) * vel_unit
        
        # metadata['spectral_model'] = re.findall(
        #     r'Spectra synthesized with the (.+)\n',
        #     header
        # )[0]
        # metadata['scattering_method'] = re.findall(
        #     r'Spectra synthesized with the .+\n# (.+)\n',
        #     header
        # )[0]
        
        metadata[PyRad.SPEC_UNIT] = u.Unit(
            re.findall(r'Spectral unit:.+\[(.+)\]\n',header)[0]
        )
        metadata[PyRad.RAD_UNIT] = u.Unit(
            re.findall(r'Radiance unit:.+\[(.+)\]\n',header)[0]
        )
        metadata[PyRad._NAMES] = re.findall(
            r'# (Wave\/freq.+)',
            header
        )[0]
        return metadata
        
    @classmethod
    def from_bytes(cls,b:bytes):
        lines = b.split(b'\n')
        header = [line.decode(settings.get_setting('encoding')) for line in lines if line.startswith(b'#')]
        content = [line.decode(settings.get_setting('encoding')) for line in lines if (not line.startswith(b'#') and len(line)>0)]
        
        metadata = cls._get_metadata('\n'.join(header))
        
        spectral_unit:u.Unit = metadata[cls.SPEC_UNIT]
        radiance_unit:u.Unit = metadata[cls.RAD_UNIT]
        
        names = metadata[cls._NAMES].split(' ')
        content = np.array(
            [
                np.fromstring(line,sep=' ') for line in content
            ]
        )
        data = {}
        for i, name in enumerate(names):
            data[name] = content[:,i] * (spectral_unit if i==0 else radiance_unit)
        return cls(data=data)
    @property
    def wl(self):
        return self['Wave/freq']