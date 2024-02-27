"""
A module to store PSG config models.
"""
from typing import Union
from astropy import units as u
from astropy.units import cds
from astropy.units import imperial

from pypsg import units as u_psg
from pypsg.cfg.base import Model
from pypsg.cfg.base import CharField, IntegerField, DateField
from pypsg.cfg.base import FloatField, QuantityField, CodedQuantityField, CharChoicesField
from pypsg.cfg.base import GeometryOffsetField, MoleculesField, AerosolsField
from pypsg.cfg.base import ProfileField, BooleanField, UnitChoicesField


class Target(Model):
    """
    PSG parameter model for keywords begining with `OBJECT`.
    """
    object = CharChoicesField('object', ('Exoplanet', 'Planet',
                              'Asteroid', 'Moon', 'Comet', 'Object'), max_length=50)
    name = CharField('object-name', max_length=50)
    date = DateField('object-date')
    diameter = QuantityField('object-diameter', u.km)
    gravity = CodedQuantityField(
        allowed_units=(u.Unit('m s-2'), u.Unit('g cm-3'), u.kg),
        unit_codes=('g', 'rho', 'kg'),
        fmt=('.4f', '.4f', '.4e'),
        names=('object-gravity', 'object-gravity-unit')
    )
    star_distance = QuantityField('object-star-distance', u.AU)
    star_velocity = QuantityField('object-star-velocity', u.Unit('km s-1'))
    solar_longitude = QuantityField('object-solar-longitude', u.deg)
    solar_latitude = QuantityField('object-solar-latitude', u.deg)
    season = QuantityField('object-season', u.deg)
    inclination = QuantityField('object-inclination', u.deg)
    position_angle = QuantityField('object-position-angle', u.deg)
    star_type = CharChoicesField(
        'object-star-type', ('O', 'B', 'A', 'F', 'G', 'K', 'M', '', '-'), max_length=1)
    star_temperature = QuantityField('object-star-temperature', u.K)
    star_radius = QuantityField('object-star-radius', u.R_sun)
    star_metallicity = FloatField('object-star-metallicity')
    obs_longitude = QuantityField('object-obs-longitude', u.deg)
    obs_latitude = QuantityField('object-obs-latitude', u.deg)
    obs_velocity = QuantityField('object-obs-velocity', u.Unit('km s-1'))
    period = QuantityField('object-period', u.day)
    orbit = CharField('object-orbit', max_length=100)

    def __init__(
        self,
        object: str = None,
        name: str = None,
        date: str = None,
        diameter: u.Quantity = None,
        gravity: u.Quantity = None,
        star_distance: u.Quantity = None,
        star_velocity: u.Quantity = None,
        solar_longitude: u.Quantity = None,
        solar_latitude: u.Quantity = None,
        season: u.Quantity = None,
        inclination: u.Quantity = None,
        position_angle: u.Quantity = None,
        star_type: str = None,
        star_temperature: u.Quantity = None,
        star_radius: u.Quantity = None,
        star_metallicity: float = None,
        obs_longitude: u.Quantity = None,
        obs_latitude: u.Quantity = None,
        obs_velocity: u.Quantity = None,
        period: u.Quantity = None,
        orbit: str = None
    ):
        super().__init__(
            object=object,
            name=name,
            date=date,
            diameter=diameter,
            gravity=gravity,
            star_distance=star_distance,
            star_velocity=star_velocity,
            solar_longitude=solar_longitude,
            solar_latitude=solar_latitude,
            season=season,
            inclination=inclination,
            position_angle=position_angle,
            star_type=star_type,
            star_temperature=star_temperature,
            star_radius=star_radius,
            star_metallicity=star_metallicity,
            obs_longitude=obs_longitude,
            obs_latitude=obs_latitude,
            obs_velocity=obs_velocity,
            period=period,
            orbit=orbit
        )


class Geometry(Model):
    """
    PSG parameter model for fields starting with `GEOMETRY`.
    """
    geometry = CharField('geometry', max_length=20)
    ref = CharField('geometry-ref', max_length=50)
    offset = GeometryOffsetField()
    observer_altitude = CodedQuantityField(
        allowed_units=(u.AU, u.km, u_psg.diameter, u.pc),
        unit_codes=('AU', 'km', 'diameter', 'pc'),
        fmt='.4f',
        names=('geometry-obs-altitude', 'geometry-altitude-unit')
    )
    azimuth = QuantityField('geometry-azimuth', u.deg)
    stellar_type = CharChoicesField(
        'geometry-stellar-type', ('O', 'B', 'A', 'F', 'G', 'K', 'M', ''), max_length=1)
    stellar_temperature = QuantityField('geometry-stellar-temperature', u.K)
    stellar_magnitude = FloatField('geometry-stellar-magnitude')
    # GEOMETRY-OBS-ANGLE -- Computed by PSG
    # GEOMETRY-SOLAR-ANGLE -- Computed by PSG
    disk_angles = IntegerField('geometry-disk-angles')
    # GEOMETRY-PLANET-FRACTION -- Computed by PSG
    # GEOMETRY-STAR-FRACTION -- Computed by PSG
    # GEOMETRY-STAR-DISTANCE -- Computed by PSG
    # GEOMETRY-ROTATION -- Computed by PSG
    # GEOMETRY-BRDFSCALER -- Computed by PSG

    def _type_to_create(self, *args, **kwargs):
        cfg = kwargs.get('cfg')
        geometry = self.geometry.read(cfg)
        if geometry is None:
            return Geometry
        if geometry == 'Observatory':
            return Observatory
        elif geometry == 'Nadir':
            return Nadir
        elif geometry == 'Limb':
            return Limb
        else:
            raise ValueError(f'Unknown geometry type {geometry}')


class Observatory(Geometry):
    """
    Observatory Geometry
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geometry.value = 'Observatory'


class Nadir(Geometry):
    """
    Nadir Geometry
    """
    zenith = QuantityField('geometry-user-param', u.deg)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geometry.value = 'Nadir'


class Limb(Geometry):
    """
    Limb Geometry
    """
    limb_altitude = QuantityField('geometry-user-param', u.km)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geometry.value = 'Limb'


class Occultation(Geometry):
    """
    Occultation Geometry
    """
    occultation_altitude = QuantityField('geometry-user-param', u.km)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geometry.value = ''
        raise NotImplementedError(
            'I don\'t know the keyword for this geometry')


class LookingUp(Geometry):
    """
    Looking Up Geometry
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geometry.value = ''
        raise NotImplementedError(
            'I don\'t know the keyword for this geometry')


class Atmosphere(Model):
    """
    Base Atmosphere model
    """
    structure = CharChoicesField(
        'atmosphere-structure', ('None', 'Equilibrium', 'Coma'))

    def _type_to_create(self, *args, **kwargs):
        cfg = kwargs.get('cfg')
        structure = self.structure.read(cfg)
        if structure is None:
            return Atmosphere
        if structure == 'None':
            return NoAtmosphere
        elif structure == 'Equilibrium':
            return EquilibriumAtmosphere
        elif structure == 'Coma':
            return ComaAtmosphere
        else:
            raise ValueError(f'Unknown atmosphere type {structure}')


class NoAtmosphere(Atmosphere):
    """
    No Atmosphere
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.structure.value = 'None'


class EquilibriumAtmosphere(Atmosphere):
    """
    An atmosphere that is in hydrostatic equilibrium.
    """
    pressure = CodedQuantityField(
        # pylint: disable-next=no-member
        allowed_units=(u.Pa, u.bar, u_psg.kbar, u_psg.mbar,
                       # pylint: disable-next=no-member
                       u_psg.ubar, cds.atm, u.torr, imperial.psi),
        unit_codes=('Pa', 'bar', 'kbar', 'mbar', 'ubar',
                    'atm', 'torr', 'psi'),  # what is `at`?
        fmt='.4e', names=('atmosphere-pressure', 'atmosphere-punit')
    )
    temperature = QuantityField('atmosphere-temperature', u.K)
    weight = QuantityField('atmosphere-weight', u.Unit('g mol-1'))
    continuum = CharField('atmosphere-continuum', max_length=300)
    molecules = MoleculesField()
    aerosols = AerosolsField()
    nmax = IntegerField('atmosphere-nmax')
    lmax = IntegerField('atmosphere-lmax')
    description = CharField('atmosphere-description', max_length=200)
    profile = ProfileField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.structure.value = 'Equilibrium'


class ComaAtmosphere(Atmosphere):
    """
    An atmosphere that is the result of outgassing.
    """
    gas_production = QuantityField('atmosphere-pressure', u.Unit('s-1'))
    at_1au = BooleanField('atmosphere-punit', true='gasau', false='gas')
    expansion_velocity = QuantityField('atmosphere-weight', u.Unit('m s-1'))
    continuum = CharField('atmosphere-continuum', max_length=300)
    molecules = MoleculesField()
    aerosols = AerosolsField()
    nmax = IntegerField('atmosphere-nmax')
    lmax = IntegerField('atmosphere-lmax')
    tau = QuantityField('atmosphere-tau', u.s)
    description = CharField('atmosphere-description', max_length=200)
    profile = ProfileField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.structure.value = 'Coma'


class Surface(Model):
    """
    The surface model.
    """
    temperature = QuantityField('surface-temperature', u.K)
    albedo = FloatField('surface-albedo')
    emissivity = FloatField('surface-emissivity')


class Generator(Model):
    """
    Combines the source and instrument models into spectra.
    """
    resolution_kernel = BooleanField('generator-resolutionkernel')
    gas_model = BooleanField('generator-gas-model')
    continuum_model = BooleanField('generator-cont-model')
    continuum_stellar = BooleanField('generator-cont-stellar')
    apply_telluric_noise = BooleanField('generator-trans-show')
    apply_telluric_obs = BooleanField('generator-trans-apply')
    telluric_params = CharField('generator-trans', max_length=20)
    rad_units = UnitChoicesField(
        'generator-radunits',
        options=tuple(value for value in u_psg.radiance_units.values()),
        codes=tuple(key for key in u_psg.radiance_units)
    )
    log_rad = BooleanField('generator-lograd')
    gcm_binning = IntegerField('generator-gcm-binning')


class Telescope(Model):
    """
    Base class for telescopes.
    """
    telescope = CharChoicesField(
        'generator-telescope',
        options=('SINGLE', 'ARRAY', 'CORONA', 'AOTF', 'LIDAR')
    )
    apperture = QuantityField('generator-diamtele', u.Unit('m'))
    zodi = FloatField('generator-telescope2')
    fov = CodedQuantityField(
        allowed_units=(u.arcsec, u.arcmin, u.deg, u.km,
                       u_psg.diameter, u_psg.diffraction),
        unit_codes=('arcsec', 'arcmin', 'deg', 'km', 'diameter', 'diffrac'),
        fmt='.4e',
        names=('generator-beam', 'generator-beamunit')
    )
    range1 = CodedQuantityField(
        allowed_units=(u.um, u.nm, u.mm, u.AA, u.Unit('cm-1'),
                       u.MHz, u.GHz, u.kHz),
        unit_codes=('um', 'nm', 'mm', 'An', 'cm', 'MHz', 'GHz', 'kHz'),
        fmt='.4e', names=('generator-range1', 'generator-rangeunit')
    )
    range2 = CodedQuantityField(
        allowed_units=(u.um, u.nm, u.mm, u.AA, u.Unit('cm-1'),
                       u.MHz, u.GHz, u.kHz),
        unit_codes=('um', 'nm', 'mm', 'An', 'cm', 'MHz', 'GHz', 'kHz'),
        fmt='.4e', names=('generator-range2', 'generator-rangeunit')
    )
    resolution = CodedQuantityField(
        allowed_units=(u_psg.resolving_power, u.um, u.nm, u.mm, u.AA,
                       u.Unit('cm-1'), u.MHz, u.GHz, u.kHz),
        unit_codes=('RP', 'um', 'nm', 'mm', 'An', 'cm', 'MHz', 'GHz', 'kHz'),
        fmt='.4e', names=('generator-resolution', 'generator-resolutionunit')
    )

    def _type_to_create(self, *args, **kwargs):
        cfg = kwargs['cfg']
        value = self.telescope.read(cfg)
        if value is None:
            return Telescope
        if value == 'SINGLE':
            return SingleTelescope
        elif value == 'ARRAY':
            return Interferometer
        elif value == 'CORONA':
            return Coronagraph
        elif value == 'AOTF':
            return AOTF
        elif value == 'LIDAR':
            return LIDAR
        else:
            raise ValueError(f'Unknown telescope type: {value}')


class Noise(Model):
    """
    Base class for noise models.
    """
    noise_type = CharChoicesField(
        'generator-noise',
        options=('NO', 'TRX', 'RMS', 'BKG', 'NEP', 'D*', 'CCD')
    )
    exp_time = QuantityField('generator-noisetime', u.s)
    n_frames = IntegerField('generator-noiseframes')
    n_pixels = FloatField(
        'generator-noisepixels',
        allow_table=True,
        xunit=u.um,
        yunit=None
    )
    desc = CharField('generator-instrument', max_length=500)

    def _type_to_create(self, *args, **kwargs):
        cfg = kwargs['cfg']
        value = self.noise_type.read(cfg)
        if value is None:
            return Noise
        if value == 'NO':
            return Noiseless
        elif value == 'TRX':
            return RecieverTemperatureNoise
        elif value == 'RMS':
            return ConstantNoise
        elif value == 'BKG':
            return ConstantNoiseWithBackground
        elif value == 'NEP':
            return PowerEquivalentNoise
        elif value == 'D*':
            return Detectability
        elif value == 'CCD':
            return CCD
        else:
            raise ValueError(f'Unknown noise type: {value}')


class SingleTelescope(Telescope):
    """
    A simple telescope with a single apperture.

    Handbook
    --------
    This mode is the classical observatory / instrument
    optical setup, in which the etendue is defined by the
    effective collecting area of the main mirror :math:`A_{Tele}`
    and its corresponding solid angle :math:`\\Omega`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telescope.value = 'SINGLE'


class Interferometer(Telescope):
    """
    An interferometry array.
    """
    n_telescopes = IntegerField('generator-telescope1')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telescope.value = 'ARRAY'


class Coronagraph(Telescope):
    """
    A coronagraph.
    """
    contrast = FloatField('generator-telescope1')
    iwa = FloatField(
        'generator-telescope3',
        allow_table=True,
        xunit=None,
        yunit=None
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telescope.value = 'CORONA'


class AOTF(Telescope):
    """
    Acousto-Optical-Tunable-Filter (AOTF)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telescope.value = 'AOTF'


class LIDAR(Telescope):
    """
    A laser source is injected into the FOV.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.telescope.value = 'LIDAR'


class Noiseless(Noise):
    """
    No noise. This is not the same as a `null` value.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'NO'


class RecieverTemperatureNoise(Noise):
    """
    Receiver temperature (radio).
    """
    temperature = QuantityField('generator-noise1', u.K)
    g_factor = FloatField('generator-noise2')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'TRX'


class ConstantNoise(Noise):
    """
    Constant noise model.
    """
    sigma = FloatField('generator-noise1')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'RMS'


class ConstantNoiseWithBackground(Noise):
    """
    No additional description in handbook.
    """
    sigma = FloatField('generator-noise1')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'BKG'


class PowerEquivalentNoise(Noise):
    """
    Noise Equivalent Power
    """
    sensitivity = QuantityField('generator-noise1', u.W/u.Hz**(1/2))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'NEP'


class Detectability(Noise):
    """
    Detectivity
    """
    sensitivity = QuantityField('generator-noise1', u.cm*u.Hz**(1/2)/u.W)
    pixel_size = QuantityField('generator-noise2', u.um)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'D*'


class CCD(Noise):
    """
    Charge image sensor (e.g., CCD, CMOS, EMCCD, ICCD / MCP)
    """
    read_noise = QuantityField(
        'generator-noise1',
        u.electron,
        allow_table=True,
        xunit=u.um,
        yunit=u.electron
    )
    dark_current = QuantityField(
        'generator-noise2',
        u.electron/u.s,
        allow_table=True,
        xunit=u.um,
        yunit=u.electron/u.s
    )
    thoughput = FloatField(
        'generator-noiseoeff',
        allow_table=True,
        xunit=u.um,
        yunit=None
    )
    emissivity = FloatField('generator-noiseoemis')
    temperature = QuantityField('generator-noiseotemp', u.K)
    pixel_depth = QuantityField('generator-noisewell', u.electron)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noise_type.value = 'CCD'
