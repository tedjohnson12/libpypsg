import astropy.units as u

radiance_units = {
    'Wsrm2um': u.Unit('W sr-1 m-2 um-1'),
    'Wsrm2cm': u.Unit('W sr-1 m-2 cm-1'),
    'Wsrm2Hz': u.Unit('W sr-1 m-2 Hz-1'),
    'Jyarc': u.Unit('Jy arcsec-2'),
    'K' : u.K,
    'KRJ': u.K,
    'Wsrm2': u.Unit('W sr-1 m-2'),
    'Ra': u.astrophys.R,
    'Wsrum': u.Unit('W sr-1 um-1'),
    'Wsrcm': u.Unit('W sr-1 cm-1'),
    'Wsr': u.Unit('W sr-1'),
    'Wum': u.Unit('W um-1'),
    'Wcm': u.Unit('W cm-1'),
    'W': u.Unit('W'),
    'ph': u.ph/u.s,
    'pt': u.ph,
    'pm': u.ph,
    'Wm2': u.Unit('W m-2'),
    'erg': u.Unit('erg s-1 cm-2'),
    'Wm2um': u.Unit('W m-2 um-1'),
    'Wm2cm': u.Unit('W m-2 cm-1'),
    'Jy': u.Jy,
    'mJy': u.mJy,
    'rel': u.dimensionless_unscaled,
    'rif': u.dimensionless_unscaled,
    'V': u.mag
}

diameter = u.def_unit('diameter')
diffraction = u.def_unit('diffraction')
resolving_power = u.def_unit('resolving_power')