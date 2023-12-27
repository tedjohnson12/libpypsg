"""
Tests for the Field-Model base functionality
"""
import pytest
from astropy import units as u
import numpy as np

from pypsg import units as u_psg

from pypsg.cfg.base import Table
from pypsg.cfg.base import Model, CharField, IntegerField
from pypsg.cfg.base import FloatField, QuantityField
from pypsg.cfg.base import DateField, CharChoicesField, GeometryOffsetField
from pypsg.cfg.base import CodedQuantityField
from pypsg.cfg.base import Molecule, MoleculesField, Aerosol, AerosolsField
from pypsg.cfg.base import Profile, ProfileField, BooleanField


def test_table():
    """
    Tests the Table class
    """
    x = np.array([1,2,3])
    y = np.array([4,5,6])
    t = Table(x,y)
    assert np.all(t.x == x)
    assert np.all(t.y == y)
    assert t.to_string(fmt='.1f') == '4.0@1.0,5.0@2.0,6.0@3.0'
    
    x = np.array([1,2,3])*u.m
    y = np.array([4,5,6])*u.K
    t = Table(x,y)
    
    with pytest.raises(TypeError):
        _ = t.to_string(fmt='.1f')
    
    assert t.to_string(xunit=u.cm, yunit=u.K, fmt='.1f') == '4.0@100.0,5.0@200.0,6.0@300.0'

def test_table_read():
    """
    Test the read method of the Table class.
    """
    cfg = '4.0@1.0,5.0@2.0,6.0@3.0'
    x,y = Table.read(cfg)
    t = Table(x,y)
    assert t.to_string(fmt='.1f') == cfg

def test_charfield():
    """
    Test the CharField class
    """
    char = CharField(max_length=4,name='char')
    char.value = 'hi'
    with pytest.raises(ValueError):
        char.value = 'hello'
    with pytest.raises(TypeError):
        char.value = 0
    char = CharField(max_length=4,name='char',null=True)
    char.value = None
    d = {'CHAR':'value'}
    assert char.read(d) == 'value'

def test_IntegerField():
    """
    Test the IntegerField class
    """
    i = IntegerField('int')
    i.value = 0
    with pytest.raises(TypeError):
        i.value = '0'
    with pytest.raises(TypeError):
        i.value = 0.
    i = IntegerField('int',null=True)
    i.value = None
    d = {'INT':0}
    assert i.read(d) == 0

def test_FloatField():
    """
    Test the FloatField class
    """
    f = FloatField('float')
    f.value = 0
    f.value = 0.
    assert f.asbytes == b'0.00'
    with pytest.raises(TypeError):
        f.value = '0'
    f = FloatField('float',null=True)
    f.value = None
    f = FloatField('float',fmt='.2e')
    f.value = 1e6
    assert f.asbytes == b'1.00e+06'
    d = {'FLOAT':0.0}
    assert f.read(d) == 0.0
    
    f = FloatField('float',fmt='.2f',allow_table=True)
    t = Table(
        np.array([1,2,3]),
        np.array([4,5,6])
    )
    f.value = t
    assert f.asbytes == b'4.00@1.00,5.00@2.00,6.00@3.00'
    
    f2 = FloatField('float2',allow_table=False)
    with pytest.raises(TypeError):
        f2.value = t
    
    d = {'FLOAT':str(f.asbytes,'utf-8')}
    t2 = f.read(d)
    assert np.all(t2.x == t.x)
    assert np.all(t2.y == t.y)

def test_QuantityField():
    """
    Test the QuantityField class
    """
    q = QuantityField('quant',u.m,null=False,allow_table=True,fmt='.2f')
    q.value = 1*u.m
    with pytest.raises(TypeError):
        q.value = 1
    with pytest.raises(ValueError):
        q.value = None
    with pytest.raises(u.UnitConversionError):
        q.value = 1*u.s
    assert q.asbytes == b'1.00'
    d = {'QUANT':1}
    assert q.read(d) == 1*u.m
    
    t = Table(
        np.array([1,2,3]),
        np.array([4,5,6])
    )
    q.value = t
    assert q.asbytes == b'4.00@1.00,5.00@2.00,6.00@3.00'
    assert q.content == b'<QUANT>4.00@1.00,5.00@2.00,6.00@3.00'
    
    d = {'QUANT':str(q.asbytes,'utf-8')}
    t2 = q.read(d)
    assert np.all(t2.x == t.x)
    assert np.all(t2.y == t.y)
    
    
    

def test_CodedQuantityField():
    """
    Test the CodedQuantityField class
    """
    g = CodedQuantityField(
        allowed_units=(u.Unit('m s-2'),u.Unit('g cm-3'), u.kg),
        unit_codes=('g', 'rho', 'kg'),
        fmt=('.4f','.4f','.4e'),
        names=('object-gravity','object-gravity-unit')
    )
    # g = GravityField()
    with pytest.raises(NotImplementedError):
        _ = g.asbytes
    with pytest.raises(NotImplementedError):
        _ = g.name
    
    g.value = 1*u.M_earth
    assert g.value == 1*u.M_earth
    g.value = 10*u.m / u.s**2
    g.value = 5*u.g / u.cm**3
    with pytest.raises(u.UnitConversionError):
        g.value = 10*u.s
    g.value = 1*u.M_earth
    # pylint: disable-next=protected-access
    val_str, unit_code = g._get_values()
    assert val_str == f'{(1*u.M_earth).to_value(u.kg):.4e}'
    assert unit_code == 'kg'
    g.value = 10*u.m / u.s**2
    # pylint: disable-next=protected-access
    val_str, unit_code = g._get_values()
    assert val_str == '10.0000'
    assert unit_code == 'g'
    g.value = 5*u.g / u.cm**3
    # pylint: disable-next=protected-access
    val_str, unit_code = g._get_values()
    assert val_str == '5.0000'
    assert unit_code == 'rho'
    assert g.content == b'<OBJECT-GRAVITY>5.0000\n<OBJECT-GRAVITY-UNIT>rho'
    g.value = 1000*u.kg
    # pylint: disable-next=protected-access
    val_str, unit_code = g._get_values()
    assert val_str == '1.0000e+03'
    
    d = {'OBJECT-GRAVITY':5,'OBJECT-GRAVITY-UNIT':'rho'}
    assert g.read(d) == 5*u.g / u.cm**3
    
    assert g.parse_unit('kg') == u.kg
    
def test_DateField():
    """
    Test the DateField class
    """
    d = DateField('date')
    d.value = '2023-08-10 14:15'
    assert d.asbytes == b'2023/08/10 14:15'
    cfg = {'DATE':'2023-08-10 14:15'}
    assert d.read(cfg) == '2023-08-10 14:15'

def test_CharChoicesField():
    """
    Test the CharChoicesField class
    """
    c = CharChoicesField('char_choice',options=['a','b'])
    c.value = 'a'
    assert c.asbytes == b'a'
    with pytest.raises(ValueError):
        c.value = 'c'
    d = {'CHAR_CHOICE':'b'}
    assert c.read(d) == 'b'

def test_GeometryOffestField():
    """
    Test the GeometryOffestField class
    """
    g = GeometryOffsetField()
    g.value = (1*u.deg, 1*u.deg)
    g.value = (1,1.4)
    with pytest.raises(u.UnitConversionError):
        g.value = (1*u.deg,1)
    expected = b'<GEOMETRY-OFFSET-NS>1.0000\n'
    expected += b'<GEOMETRY-OFFSET-EW>1.4000\n'
    expected += b'<GEOMETRY-OFFSET-UNIT>diameter'
    assert g.content == expected
    d = {'GEOMETRY-OFFSET-NS':1,'GEOMETRY-OFFSET-EW':1.4,'GEOMETRY-OFFSET-UNIT':'diameter'}
    assert g.read(d) == (1,1.4)

def test_Molecule():
    """
    Test the Molecule class
    """
    mol = Molecule('H2O','HIT[1]',1*u.pct)
    assert mol.abn == pytest.approx(1.0,abs=1e-6)
    assert mol.unit_code == '%'
    assert Molecule.get_abn_unit(mol.unit_code) == u.pct
    mol = Molecule('H2O', 'HIT[1]',1)
    assert mol.abn == pytest.approx(1.0,abs=1e-6)
    assert mol.unit_code == 'scl'
    assert Molecule.get_abn_unit(mol.unit_code) == u.dimensionless_unscaled
    

def test_Aerosol():
    """
    Test the Aerosol class
    """
    aero = Aerosol('Water','watertype',1.0,1*u.um)
    assert aero.abn == pytest.approx(1.00,abs=1e-6)
    assert aero.unit_code == 'scl'
    assert Aerosol.get_abn_unit(aero.unit_code) == u.dimensionless_unscaled
    assert aero.size == pytest.approx(1.00,abs=1e-6)
    assert aero.size_unit_code == 'um'
    assert Aerosol.get_size_unit(aero.size_unit_code) == u.um
    
    aero = Aerosol('Water','watertype',1*u.pct,4*u.LogUnit(u.um))
    assert aero.abn == pytest.approx(1.0,abs=1e-6)
    assert aero.unit_code == '%'
    assert Aerosol.get_abn_unit(aero.unit_code) == u.pct
    assert aero.size == pytest.approx(4.00,abs=1e-6)
    assert aero.size_unit_code == 'lum'
    assert Aerosol.get_size_unit(aero.size_unit_code) == u.LogUnit(u.um)



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

def test_BooleanField():
    b = BooleanField('boolean')
    with pytest.raises(TypeError):
        b.value = 1
    b.value = True
    assert b.content == b'<BOOLEAN>Y'
    b = BooleanField('boolean',true='yes',false='no')
    b.value = False
    assert b.content == b'<BOOLEAN>no'

    
def test_model():
    class TestModel(Model):
        name = CharField(name='name',max_length=30)
        age = IntegerField('age',default=0,null=True)
    
    person = TestModel(name='Ted', age=23)
    person.age:IntegerField
    assert isinstance(person.name,CharField)
    assert person.name.asbytes == b'Ted'
    assert person.name.content == b'<NAME>Ted'
    assert person.age.asbytes == b'23'
    assert person.age.content == b'<AGE>23'
    expected = b'<AGE>23\n<NAME>Ted'
    assert person.content == expected
    
    person2 = TestModel(name='Cactus')
    assert person2.name.asbytes == b'Cactus'
    assert person2.name.content == b'<NAME>Cactus'
    assert person2.age.asbytes == b'0'
    assert person2.age.content == b'<AGE>0'
    person2.age.value = 3
    assert person2.age.asbytes == b'3'
    
    assert person.name.asbytes == b'Ted'
    
    class OtherModel(Model):
        name = CharField(name='name',max_length=30)
        def __init__(self,favorite_color,name=None):
            super().__init__(name=name)
            self.favorite_color = favorite_color
            
    person3 = OtherModel(name='Barbie',favorite_color='#e0218a')
    assert person3.name.asbytes == b'Barbie'
    assert person3.favorite_color == '#e0218a'
    
    expected = b'<NAME>Barbie'
    assert person3.content == expected


if __name__ in '__main__':
    pytest.main(args=[__file__])
    