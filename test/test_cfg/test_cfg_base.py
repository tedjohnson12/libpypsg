"""
Tests for the Field-Model base functionality
"""
import pytest
from astropy import units as u

from pypsg.cfg.base import Field, Model, CharField, IntegerField
from pypsg.cfg.base import FloatField, QuantityField

def test_field():
    field = Field(
        name='test'
    )
    assert field.is_null
    assert field.default is None
    assert field.null is False
    
    field.value = 2
    assert not field.is_null
    assert field._value == 2
    assert field.value == b'2'
    assert field.content == b'<TEST>2'
    
    with pytest.raises(ValueError):
        field.value = None
    ####
    field = Field(
        name='test',
        default=3,
        null=False
    )
    assert field.default == 3
    assert field.null is False

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
    q = QuantityField('quant',u.m)
    q.value = 1*u.m
    with pytest.raises(TypeError):
        q.value = 1
    with pytest.raises(ValueError):
        q.value = None
    with pytest.raises(u.UnitConversionError):
        q.value = 1*u.s
    assert q.value == b'1.00'
    
    
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


if __name__ in '__main__':
    test_model()
    