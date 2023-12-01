"""
PSG Layer files
"""
from typing import Tuple, List
import re
import numpy as np
from astropy import units as u

from pypsg.cfg.base import Profile
from pypsg import settings

class PyLyr:
    """
    Python representation of lyr files.
    """

    def __init__(self, *profiles: Profile):
        self.profiles: Tuple[Profile] = profiles
    
    @classmethod
    def from_bytes(cls, b: bytes):
        s = b.decode(settings.get_setting('encoding'))
        lines = s.split('\n')
        save = False
        saved_lines:List[str] = []
        for line in lines:
            if 'Alt[km]' in line:
                save = True
            if save:
                if '--' in line:
                    if len(saved_lines) > 2:
                        save = False
                    else:
                        pass
                else:
                    saved_lines.append(line[2:-1])
        del lines
        if len(saved_lines) == 0:
            raise ValueError('No data was captured. Perhaps the format is wrong.')
        dat = np.array(
            [np.fromstring(line, sep=' ',) for line in saved_lines[1:]]
        )
        names = saved_lines[0].split()
        for i, name in enumerate(names):
            # get previous parameter (e.g 'water' for 'water_size')
            if 'size' in name:
                names[i] = names[i-1] + '_' + name
        unit_code = [re.findall(r'\[([\w\d\/\-\^])\]',name)[0] for name in names]
        units = [u.Unit(code) for code in unit_code]
        profiles = [
            Profile(name,dat[i,:],unit) for i,(name,unit) in enumerate(zip(names,units)) 
        ]
        return cls(*profiles)
    @property
    def to_dataframe(self):
        import pandas as pd
        def get_name(name:str,unit:u.Unit):
            return f'{name} [{unit.to_string()}]'
        return pd.DataFrame({get_name(profile.name,profile.unit):profile.dat for profile in self.profiles})
    
        