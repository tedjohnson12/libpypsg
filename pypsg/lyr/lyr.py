"""
PSG Layer files
"""
from typing import Tuple, List
from pathlib import Path
import re
import numpy as np
from astropy import units as u
from astropy.table import QTable
from astropy.io import fits

from pypsg.cfg.base import Profile
from pypsg import settings

class PyLyr:
    """
    Python representation of lyr files.
    """
    PROF_EXT = 'PROFILE'
    CG_EXT = "CG"
    def __init__(
        self,
        prof:QTable,
        cg:QTable
    ):
        self.prof = prof
        self.prof.meta['EXTNAME'] = self.PROF_EXT
        self.cg = cg
        self.cg.meta['EXTNAME'] = self.CG_EXT
    
    @staticmethod
    def _parse(text:str)->Tuple[dict,str,str,str]:
        metadata = {}
        other_data = {}
        def find(s:str):
            """TODO: Change all below to use this func.
            If something break this is probably why."""
            try:
                return re.findall(s,text)[0]
            except IndexError:
                return None
        # metadata['source'] = re.findall(r'# (NASA-GSFC.*)',text)[0]
        # metadata['scattering'] = re.findall(r'# (.*), LMAX',text)[0]
        # metadata['date'] = re.findall(r'# Synthesized on (.*)',text)[0]
        # metadata['rad_tran_method'] = re.findall(r'# Radiative transfer method: (.*)',text)[0]
        # syn_res_unit = u.Unit(
        #     re.findall(r'# Synthesis resolution \[(.*)\]',text)[0]
        # )
        # syn_res_val, l_over_dl, points, fine_scalar =  re.findall(
        #     r'# Synthesis resolution .*: (.*)',text
        # )[0].split(' ')
        # metadata['syn_res'] = float(syn_res_val) * syn_res_unit
        # metadata['l_over_dl'] = float(l_over_dl)
        # metadata['points'] = float(points)
        # metadata['fine_scalar'] = float(fine_scalar)
        
        # metadata['profile_source'] = re.findall(r'# Molecular abundance profile: (.*)',text)[0]
        metadata['molecules'] = re.findall(r'# Molecules considered: (.*)',text)[0]
        metadata['molec_sources'] = re.findall(r'# Molecular sources: (.*)',text)[0]
        metadata['molec_abuns'] = re.findall(r'# Molecular abundances: (.*)',text)[0]
        metadata['molec_abun_units'] = re.findall(r'# Molecular abundance units: (.*)',text)[0]
        # metadata['collisional'] = re.findall(r'# Collissional partners (.*)',text)[0]
        # metadata['uv_cross_sections'] = find(r'UV cross-sections included: (.*)')
        # metadata['cia'] = re.findall(r'# Collision-Induced-Absorption: (.*)',text)[0]
        # metadata['molec_rayleigh'] = re.findall(r'# Molecular Rayleigh (.*)',text)[0]
        # rmax_minus_1, bending = re.findall(r'# Refraction .*: (.*)',text)[0].split(' ')
        # bending_unit = u.Unit(re.findall(r'# Refraction .* bending \[(.*)\]',text)[0])
        # metadata['rmax_minus_1'] = float(rmax_minus_1)
        # metadata['bending'] = float(bending) * bending_unit
        
        metadata['aerosols'] = find(r'Aerosols considered: (.*)')
        metadata['aero_sources'] = find(r'Aerosols sources: (.*)')
        metadata['aero_abns'] = find(r'Aerosols abundances: (.*)')
        metadata['aero_abn_units'] = find(r'Aerosol abundance units: (.*)')
        metadata['aero_sizes'] = find(r'Aerosol sizes: (.*)')
        metadata['aero_size_units'] = find(r'Aerosol size units: (.*)')
        
        other_data['tab1_names'] = re.findall(r'#[ ]*(Alt\[km\].*)',text)[0]
        other_data['tab2_names'] = re.findall(r'#[ ]*(Alt\[km\].*)',text)[0]
        

        possible_table_lines =re.compile(r"(#[ ]+[\de\-\+\.\s]+)\n").findall(text,re.MULTILINE)
        tabs = []
        current_tab = []
        for line in possible_table_lines:
            if not '.' in line:
                if len(current_tab) == 0:
                    pass
                else:
                    tabs.append(current_tab)
                    current_tab = []
            else:
                current_tab.append(line)
        tab1_raw = '\n'.join(tabs[0])
        tab2_raw = '\n'.join(tabs[1])
                
        
        # tab1_raw = re.findall(
        #     r'Alt.*\n.*\n((# +\d[ \d.einf\-\+]+\n)+)',
        #     text
        # )[0]
        
        # tab2_raw = re.findall(
        #     r'Low.*\n.*\n((# +\d[ \d.einf\-\+]+\n)+)',
        #     text
        # )[0]
        
        integrated_vals = re.findall(
            r'Integrated[a-z ]+(.*)',text
        )[0]
        return metadata, other_data, tab1_raw, tab2_raw, integrated_vals
    
    @staticmethod
    def _get_tab_cols(
        raw_names:list,
        molec_unit : u.Unit,
        aero_unit : u.Unit,
        molecs:list = None,
        aeros:list = None
        )->Tuple[List[str],List[u.Unit]]:
        
        
        molecs = [] if molecs is None else molecs
        aeros = [] if aeros is None else aeros
        
        names = []
        units = []
        
        for i, name in enumerate(raw_names):
            try:
                unit = u.Unit(re.findall(r'\[(.*)\]',name)[0])
            except IndexError:
                unit = u.dimensionless_unscaled
            if name in molecs:
                names.append(name)
                units.append(molec_unit)
            elif name in aeros:
                names.append(name)
                units.append(aero_unit)
            elif 'size' in name:
                prev_name = raw_names[i-1]
                names.append(f'{prev_name}_size')
                units.append(unit)
            else:
                names.append(name.split('[')[0])
                units.append(unit)
        return names, units
    @staticmethod
    def _parse_tab_data(tab_raw:str)->np.ndarray:
        return np.array([
            np.fromstring(line[1:],sep=' ') for line in tab_raw.split('\n')
        ])
    
    @staticmethod
    def _build_tab(
        names:List[str],
        units:List[u.Unit],
        data:np.ndarray,
        meta:dict = None
    )->QTable:
        dat = {}
        for i,(name,unit) in enumerate(zip(names,units)):
            dat[name] = data[:,i]*unit
        return QTable(dat,meta=meta)
        
    
    
    @classmethod
    def from_bytes(cls, b: bytes):
        """
        From a bytes object read from a .lyr file
        """
        s = b.decode(settings.get_setting('encoding'))
        
        metadata, other_data, tab1_raw, tab2_raw, integrated_vals = cls._parse(s)
        tab1_names, tab1_units = cls._get_tab_cols(
            other_data['tab1_names'].split(),
            u.dimensionless_unscaled,
            u.dimensionless_unscaled,
            molecs=metadata['molecules'],
            aeros=metadata['aerosols']
        )
        tab1_dat = cls._parse_tab_data(tab1_raw)
        
        tab2_names, tab2_units = cls._get_tab_cols(
            other_data['tab2_names'].split(),
            u.m**-2,
            u.kg*u.m**-2,
            molecs=metadata['molecules'],
            aeros=metadata['aerosols']
        )
        tab2_dat = cls._parse_tab_data(tab2_raw)
        
        tab1 = cls._build_tab(
            tab1_names,
            tab1_units,
            tab1_dat,
            # meta=metadata
        )
        tab2 = cls._build_tab(
            tab2_names,
            tab2_units,
            tab2_dat,
        )
        return cls(
            prof=tab1,
            cg=tab2
        )
    def to_fits(self,path:Path):
        """
        Write to a fits file.
        """
        # hdulist = fits.HDUList()
        # prof_hdu = fits.table_to_hdu(self.prof)
        self.prof.write(path,overwrite=True)
        self.cg.write(path,append=True)
        # prof_hdu.header['EXTNAME'] = self.PROF_EXT
        # hdulist.append(prof_hdu)
        
        # cg_hdu = fits.table_to_hdu(self.cg)
        # cg_hdu.header['EXTNAME'] = self.CG_EXT
        # hdulist.append(cg_hdu)
        
        # hdulist.writeto(path,overwrite=True)
    @classmethod
    def from_fits(cls,path:Path):
        with fits.open(path) as hdulist:
            prof_table = QTable.read(hdulist[cls.PROF_EXT])
            cg_table = QTable.read(hdulist[cls.CG_EXT])
            
        return cls(prof=prof_table, cg=cg_table)
