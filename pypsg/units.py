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
    s=['pbv','ppb'],
    represents=1e-9*u.dimensionless_unscaled,
    doc='part per billion'
)
pptv = u.def_unit(
    s=['pptv','ppt'],
    represents=1e-12*u.dimensionless_unscaled,
    doc='part per trillion'
)
kbar = u.def_unit(
    s=['kbar'],
    represents=1e3*u.bar,
    doc='kilobar'
)
mbar = u.def_unit(
    s=['mbar'],
    represents=1e-3*u.bar,
    doc='milibar'
)
ubar = u.def_unit(
    s=['ubar'],
    represents=1e-6*u.bar,
    doc='microbar'
)