"""
Store the units to convert between Quantities and floats.
"""

from astropy import units as u

CFG_UNITS = {
    'OBJECT-STAR-DISTANCE': {'unit':'AU','fmt':'.2f'},
    'OBJECT-STAR-VELOCITY': {'unit':'km s-1','fmt':'.2f'},
}