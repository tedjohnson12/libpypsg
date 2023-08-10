"""
Tests for the Field-Model base functionality
"""
import pytest
from astropy import units as u

from pypsg.cfg.base import Field, Model, CharField, IntegerField
from pypsg.cfg.base import FloatField, QuantityField, GravityField
from pypsg.cfg.base import DateField, CharChoicesField

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

def test_GravityField():
    g = GravityField()
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
    assert val_str == f'{(1*u.M_earth).to_value(u.kg):.4f}'
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
    