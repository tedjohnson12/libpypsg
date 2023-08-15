"""
A custom set of units to use in pypsg
"""

from astropy import units as u

ppmv = u.def_unit(
    s=['ppmv','ppm'],
    represents=1e-6*u.dimensionless_unscaled,
    doc='part per million'
)
ppbv = u.def_unit(
    s=['ppbv','ppb'],
    represents=1e-9*u.dimensionless_unscaled,
    doc='part per billion'
)
pptv = u.def_unit(
    s=['pptv','ppt'],
    represents=1e-12*u.dimensionless_unscaled,
    doc='part per trillion'
)