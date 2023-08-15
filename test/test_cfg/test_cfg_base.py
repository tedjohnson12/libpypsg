"""
Tests for the Field-Model base functionality
"""
import pytest
from astropy import units as u
import numpy as np

from pypsg import units as u_psg

from pypsg.cfg.base import Field, Model, CharField, IntegerField
from pypsg.cfg.base import FloatField, QuantityField
from pypsg.cfg.base import DateField, CharChoicesField, GeometryOffsetField
from pypsg.cfg.base import CodedQuantityField, MultiQuantityField
from pypsg.cfg.base import Molecule, MoleculesField, Aerosol, AerosolsField
from pypsg.cfg.base import Profile, ProfileField

def test_field():
    field = Field(
        name='test'
    )
    assert field.is_null
    assert field.default is None
    assert field.null is True
    
    field.value = 2
    assert not field.is_null
    assert field._value == 2
    assert field.value == b'2'
    assert field.content == b'<TEST>2'
    
    
    ####
    field = Field(
        name='test',
        default=3,
        null=False
    )
    assert field.default == 3
    assert field.null is False
    with pytest.raises(ValueError):
        field.value = None

def test_CharField():
    char = CharField(max_length=4,name='char')
    char.value = 'hi'
    with pytest.raises(ValueError):
        char.value = 'hello'
    with pytest.raises(TypeError):
        char.value = 0
    char = CharField(max_length=4,name='char',null=True)
    char.value = None

def test_IntegerField():
    i = IntegerField('int')
    i.value = 0
    with pytest.raises(TypeError):
        i.value = '0'
    with pytest.raises(TypeError):
        i.value = 0.
    i = IntegerField('int',null=True)
    i.value = None

def test_FloatField():
    f = FloatField('float')
    f.value = 0
    f.value = 0.
    assert f.value == b'0.00'
    with pytest.raises(TypeError):
        f.value = '0'
    f = FloatField('float',null=True)
    f.value = None
    f = FloatField('float',fmt='.2e')
    f.value = 1e6
    assert f.value == b'1.00e+06'

def test_QuantityField():
    q = QuantityField('quant',u.m,null=False)
    q.value = 1*u.m
    with pytest.raises(TypeError):
        q.value = 1
    with pytest.raises(ValueError):
        q.value = None
    with pytest.raises(u.UnitConversionError):
        q.value = 1*u.s
    assert q.value == b'1.00'

def test_CodedQuantityField():
    g = CodedQuantityField(
        allowed_units=(u.Unit('m s-2'),u.Unit('g cm-3'), u.kg),
        unit_codes=('g', 'rho', 'kg'),
        fmt=('.4f','.4f','.4e'),
        names=('object-gravity','object-gravity-unit')
    )
    # g = GravityField()
    with pytest.raises(NotImplementedError):
        _ = g.value
    with pytest.raises(NotImplementedError):
        _ = g.name
    
    g.value = 1*u.M_earth
    assert g._value == 1*u.M_earth
    g.value = 10*u.m / u.s**2
    g.value = 5*u.g / u.cm**3
    with pytest.raises(u.UnitConversionError):
        g.value = 10*u.s
    g.value = 1*u.M_earth
    val_str, unit_code = g._get_values()
    assert val_str == f'{(1*u.M_earth).to_value(u.kg):.4e}'
    assert unit_code == 'kg'
    g.value = 10*u.m / u.s**2
    val_str, unit_code = g._get_values()
    assert val_str == '10.0000'
    assert unit_code == 'g'
    g.value = 5*u.g / u.cm**3
    val_str, unit_code = g._get_values()
    assert val_str == '5.0000'
    assert unit_code == 'rho'
    assert g.content == b'<OBJECT-GRAVITY>5.0000\n<OBJECT-GRAVITY-UNIT>rho'
    g.value = 1000*u.kg
    val_str, unit_code = g._get_values()
    assert val_str == '1.0000e+03'
    
def test_DateField():
    d = DateField('date')
    d.value = '2023-08-10 14:15'
    assert d.value == b'2023/08/10 14:15'

def test_CharChoicesField():
    c = CharChoicesField('char_choice',options=['a','b'])
    c.value = 'a'
    assert c.value == b'a'
    with pytest.raises(ValueError):
        c.value = 'c'

def test_GeometryOffestField():
    g = GeometryOffsetField()
    g.value = (1*u.deg, 1*u.deg)
    g.value = (1,1.4)
    with pytest.raises(u.UnitConversionError):
        g.value = (1*u.deg,1)
    expected = b'<GEOMETRY-OFFSET-NS>1.0000\n'
    expected += b'<GEOMETRY-OFFSET-EW>1.4000\n'
    expected += b'<GEOMETRY-OFFSET-UNIT>diameter'
    assert g.content == expected

def test_MultiQuantityField():
    m = MultiQuantityField('field',(u.s,u.km),fmt='.2f')
    m.value = 1*u.min
    assert m.value == b'60.00'
    m.value = 100*u.m
    assert m.value == b'0.10'
    with pytest.raises(u.UnitTypeError):
        m.value = 1*u.kg

def test_Molecule():
    mol = Molecule('H2O','HIT[1]',1*u.pct)
    assert mol.abn == pytest.approx(1.0,abs=1e-6)
    assert mol.unit_code == '%'
    mol = Molecule('H2O', 'HIT[1]',1)
    assert mol.abn == pytest.approx(1.0,abs=1e-6)
    assert mol.unit_code == 'scl'

def test_Aerosol():
    aero = Aerosol('Water','watertype',1.0,1*u.um)
    assert aero.abn == pytest.approx(1.00,abs=1e-6)
    assert aero.unit_code == 'scl'
    assert aero.size == pytest.approx(1.00,abs=1e-6)
    assert aero.size_unit_code == 'um'
    aero = Aerosol('Water','watertype',1*u.pct,4*u.LogUnit(u.um))
    assert aero.abn == pytest.approx(1.0,abs=1e-6)
    assert aero.unit_code == '%'
    assert aero.size == pytest.approx(4.00,abs=1e-6)
    assert aero.size_unit_code == 'lum'



def test_MoleculeField():
    mol = Molecule('H2O','HIT[1]',1*u.pct)
    m = MoleculesField()
    m.value = (mol,)
    with pytest.raises(NotImplementedError):
        m._str_property
    assert m._ngas == 1
    assert m.ngas == '<ATMOSPHERE-NGAS>1'    
    assert m.gas == '<ATMOSPHERE-GAS>H2O'
    assert m.type == '<ATMOSPHERE-TYPE>HIT[1]'
    assert m.abun == '<ATMOSPHERE-ABUN>1.00e+00'
    assert m.unit == '<ATMOSPHERE-UNIT>%'
    expected = b'<ATMOSPHERE-NGAS>1\n'
    expected += b'<ATMOSPHERE-GAS>H2O\n'
    expected += b'<ATMOSPHERE-TYPE>HIT[1]\n'
    expected += b'<ATMOSPHERE-ABUN>1.00e+00\n'
    expected += b'<ATMOSPHERE-UNIT>%'
    assert m.content == expected

    mol2 = Molecule('CO2','HIT[2]',1)
    m.value = (mol,mol2)
    assert m._ngas == 2
    assert m.ngas == '<ATMOSPHERE-NGAS>2'    
    assert m.gas == '<ATMOSPHERE-GAS>H2O,CO2'
    assert m.type == '<ATMOSPHERE-TYPE>HIT[1],HIT[2]'
    assert m.abun == '<ATMOSPHERE-ABUN>1.00e+00,1.00e+00'
    assert m.unit == '<ATMOSPHERE-UNIT>%,scl'
    expected = b'<ATMOSPHERE-NGAS>2\n'
    expected += b'<ATMOSPHERE-GAS>H2O,CO2\n'
    expected += b'<ATMOSPHERE-TYPE>HIT[1],HIT[2]\n'
    expected += b'<ATMOSPHERE-ABUN>1.00e+00,1.00e+00\n'
    expected += b'<ATMOSPHERE-UNIT>%,scl'
    assert m.content == expected

def test_AerosolField():
    aeros = (
        Aerosol('Water','water_dat',1.0,1.0),
        Aerosol('WaterIce','waterice_dat',10*u_psg.ppmv,3*u.LogUnit(u.um))
    )
    a = AerosolsField()
    a.value = aeros
    assert a._naero == 2
    assert a.naero == '<ATMOSPHERE-NAERO>2'    
    assert a.aeros == '<ATMOSPHERE-AEROS>Water,WaterIce'
    assert a.type == '<ATMOSPHERE-ATYPE>water_dat,waterice_dat'
    assert a.abun == '<ATMOSPHERE-AABUN>1.00e+00,1.00e+01'
    assert a.unit == '<ATMOSPHERE-AUNIT>scl,ppmv'
    assert a.size == '<ATMOSPHERE-ASIZE>1.00e+00,3.00e+00'
    assert a.size_unit == '<ATMOSPHERE-ASUNI>scl,lum'
    expected = b'<ATMOSPHERE-NAERO>2\n'
    expected += b'<ATMOSPHERE-AEROS>Water,WaterIce\n'
    expected += b'<ATMOSPHERE-ATYPE>water_dat,waterice_dat\n'
    expected += b'<ATMOSPHERE-AABUN>1.00e+00,1.00e+01\n'
    expected += b'<ATMOSPHERE-AUNIT>scl,ppmv\n'
    expected += b'<ATMOSPHERE-ASIZE>1.00e+00,3.00e+00\n'
    expected += b'<ATMOSPHERE-ASUNI>scl,lum'
    assert a.content == expected

def test_profile():
    p = Profile('H2O',np.array([1.,1.]))
    assert np.all(p.dat == [1,1]*u.dimensionless_unscaled)
    assert p.nlayers == 2
    assert p.fget_layer(0) == 1.
    assert not (p.is_temperature or p.is_pressure)

    p = Profile('T',np.array([300.,200.]),unit=u.K)
    assert p.is_temperature
    assert not p.is_pressure
    assert p.get_layer(1) == 200*u.K

    p = Profile('Press',np.array([1.,0.1]),unit=u.bar)
    assert not p.is_temperature
    assert p.is_pressure
    assert p.get_layer(0) == 1*u.bar

def test_ProfileField():
    press = Profile('Press',np.array([1.,0.1,0.01]),unit=u.bar)
    temp = Profile('Temp',np.array([300,250,200]),unit=u.K)
    h2o = Profile('H2O',np.array([1.,0.7,1.]))
    co2 = Profile('CO2',np.array([0.0,0.3]))
    p = ProfileField()
    with pytest.raises(ValueError):
        p.value = (press,temp,co2)
    with pytest.raises(ValueError):
        p.value = (press,h2o)
    with pytest.raises(ValueError):
        p.value = (temp,h2o)
    p.value = (press,temp,h2o)
    assert p.get_molecules(0) == [1.0]
    assert p.get_temperature(0) == 300
    assert p.get_temperature(2) == 200
    assert p.get_pressure(0) == 1.
    assert p.get_pressure(1) == 0.1
    assert p.names == '<ATMOSPHERE-LAYERS-MOLECULES>H2O'
    assert p.nlayers == 3
    assert p.str_nlayers == '<ATMOSPHERE-LAYERS>3'
    assert p.get_layer(0) == '<ATMOSPHERE-LAYER-1>1.000000e+00,3.000000e+02,1.000000e+00'
    expected = b'<ATMOSPHERE-LAYERS-MOLECULES>H2O\n'
    expected += b'<ATMOSPHERE-LAYERS>3\n'
    expected += b'<ATMOSPHERE-LAYER-1>1.000000e+00,3.000000e+02,1.000000e+00\n'
    expected += b'<ATMOSPHERE-LAYER-2>1.000000e-01,2.500000e+02,7.000000e-01\n'
    expected += b'<ATMOSPHERE-LAYER-3>1.000000e-02,2.000000e+02,1.000000e+00'
    assert p.content == expected
    
def test_model():
    class TestModel(Model):
        name = CharField(name='name',max_length=30)
        age = IntegerField('age',default=0,null=True)
    
    person = TestModel(name='Ted', age=23)
    assert isinstance(person.name,CharField)
    assert person.name.value == b'Ted'
    assert person.name.content == b'<NAME>Ted'
    assert person.age.value == b'23'
    assert person.age.content == b'<AGE>23'
    expected = b'<NAME>Ted\n<AGE>23'
    assert person.content == expected
    
    person2 = TestModel(name='Cactus')
    assert person2.name.value == b'Cactus'
    assert person2.name.content == b'<NAME>Cactus'
    assert person2.age.value == b'0'
    assert person2.age.content == b'<AGE>0'
    person2.age = 3
    assert person2.age.value == b'3'
    
    assert person.name.value == b'Ted'
    
    class OtherModel(Model):
        name = CharField(name='name',max_length=30)
        def __init__(self,favorite_color,name=None):
            super().__init__(name=name)
            self.favorite_color = favorite_color
            
    person3 = OtherModel(name='Barbie',favorite_color='#e0218a')
    assert person3.name.value == b'Barbie'
    assert person3.favorite_color == '#e0218a'
    
    expected = b'<NAME>Barbie'
    assert person3.content == expected


if __name__ in '__main__':
    test_model()
    