"""
A module to store PSG config models.
"""
from astropy import units as u

from pypsg.cfg.base import Model
from pypsg.cfg.base import Field, CharField, IntegerField, DateField
from pypsg.cfg.base import FloatField, QuantityField, CodedQuantityField, CharChoicesField
from pypsg.cfg.base import GeometryOffsetField, MultiQuantityField


class Target(Model):
    """
    PSG parameter model for keywords begining with `OBJECT`.
    """
    object = CharChoicesField('object',('Exoplanet','Planet','Asteroid','Moon','Comet','Object'),max_length=50)
    name = CharField('object-name',max_length=50)
    date = DateField('object-date')
    diameter = QuantityField('object-diameter',u.km)
    gravity = CodedQuantityField(
        allowed_units=(u.Unit('m s-2'),u.Unit('g cm-3'), u.kg),
        unit_codes=('g', 'rho', 'kg'),
        fmt=('.4f','.4f','.4e'),
        names=('object-gravity','object-gravity-unit')
    )
    star_distance = QuantityField('object-star-distance',u.AU)
    star_velocity = QuantityField('object-star-velocity',u.Unit('km s-1'))
    solar_longitude = QuantityField('object-solar-longitude',u.deg)
    solar_latitude = QuantityField('object-solar-latitude',u.deg)
    season = QuantityField('object-season',u.deg)
    inclination = QuantityField('object-inclination',u.deg)
    position_angle = QuantityField('object-position-angle',u.deg)
    star_type = CharChoicesField('object-star-type',('O','B','A','F','G','K','M',''),max_length=1)
    star_temperature = QuantityField('object-star-temperature',u.K)
    star_radius = QuantityField('object-star-radius',u.R_sun)
    star_metallicity = FloatField('object-star-metallicity')
    obs_longitude = QuantityField('object-obs-longitude',u.deg)
    obs_latitude = QuantityField('object-obs-latitude',u.deg)
    obs_velocity = QuantityField('object-obs-velocity',u.Unit('km s-1'))
    period = QuantityField('object-period',u.day)
    orbit = CharField('object-orbit',max_length=100)

class Geometry(Model):
    """
    PSG parameter model for fields starting with `GEOMETRY`.
    """
    geometry = CharField('geometry',max_length=20)
    ref = CharField('geometry-ref',max_length=50)
    offset = GeometryOffsetField()
    obs_altitude = CodedQuantityField(
        allowed_units=(u.AU,u.km,u.dimensionless_unscaled,u.pc),
        unit_codes=('AU','km','diameter','pc'),
        fmt='.4f',
        names=('geometry-obs-altitude','geometry-altitude-unit')
    )
    azimuth = QuantityField('geometry-azimuth',u.deg)
    user_parameter = MultiQuantityField('geometry-user-parameter',(u.deg,u.km))
    stellar_type = CharChoicesField('geometry-stellar-type',('O','B','A','F','G','K','M',''),max_length=1)
    stellar_temperature = QuantityField('geometry-stellar-temperature',u.K)
    stellar_magnitude = FloatField('geometry-stellar-magnitude')
    # GEOMETRY-OBS-ANGLE -- Computed by PSG
    # GEOMETRY-SOLAR-ANGLE -- Computed by PSG
    disk_angles = IntegerField('geometry-disk-angles')
    # GEOMETRY-PLANET-FRACTION -- Computed by PSG
    # GEOMETRY-STAR-FRACTION -- Computed by PSG
    # GEOMETRY-STAR-DISTANCE -- Computed by PSG
    # GEOMETRY-ROTATION -- Computed by PSG
    # GEOMETRY-BRDFSCALER -- Computed by PSG

class Atmosphere(Model):
    structure = CharChoicesField('atmosphere-structure',('None','Equilibrium','Coma'))
    