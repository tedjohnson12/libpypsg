"""
A module to store PSG config models.
"""
from astropy import units as u

from pypsg.cfg.base import Model
from pypsg.cfg.base import Field, CharField, IntegerField, DateField
from pypsg.cfg.base import FloatField, QuantityField, GravityField, CharChoicesField


class Target(Model):
    """
    PSG parameter model for keywords begining with `OBJECT`.
    """
    object = CharChoicesField('object',('Exoplanet','Planet','Asteroid','Moon','Comet','Object'),max_length=50)
    name = CharField('object-name',max_length=50)
    date = DateField('object-date')
    diameter = QuantityField('object-diameter',u.km)