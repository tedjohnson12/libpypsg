"""
Transmitance module
"""

from pathlib import Path
import re
import numpy as np

import astropy.units as u
from astropy import table

from pypsg import settings


class PyTrn(table.QTable):
    """
    A python representation for `.trn` files.
    """
    SPEC_UNIT = 'SPECUNIT'
    _NAMES = 'NAMES'
    @staticmethod
    def _get_metadata(header:str):
        """
        Get the metadata from the header.
        """
        metadata = {}
        metadata[PyTrn.SPEC_UNIT] = u.Unit(
            re.findall(r'Spectral unit:.+\[(.+)\]\n',header)[0]
        )
        metadata[PyTrn._NAMES] = re.findall(
            r'# (Wave\/freq.+)',
            header
        )[0]
        return metadata
    
    @classmethod
    def from_bytes(cls, b:bytes):
        """
        Load a `.trn` file from a bytes object.
        """
        b = b.replace(b'\r',b'')
        lines = b.split(b'\n')
        header = [line.decode(settings.get_setting('encoding')) for line in lines if line.startswith(b'#')]
        content = [line.decode(settings.get_setting('encoding')) for line in lines if (not line.startswith(b'#') and len(line)>0)]
        
        metadata = cls._get_metadata('\n'.join(header))
        
        names = metadata[cls._NAMES].split(' ')
        wl_unit:u.Unit = metadata[cls.SPEC_UNIT]
        trn_unit = u.dimensionless_unscaled
        
        content = np.array(
            [
                np.fromstring(line,sep=' ') for line in content
            ]
        )
        data = {}
        for i, name in enumerate(names):
            data[name] = content[:,i] * (wl_unit if i==0 else trn_unit)
        return cls(data=data)
    
    @classmethod
    def from_file(cls, path:Path):
        """
        
        """
        with open(path,'rb') as file:
            content = file.read()
        return cls.from_bytes(content)
    
    @property
    def wl(self):
        return self['Wave/freq']
    
    def __getitem__(self, item:str)->u.Quantity:
        return super().__getitem__(item)