"""
This module contains the basic functionality for fields in PSG
config objects.
"""
from typing import Any,Tuple
from copy import deepcopy
from astropy import units as u
from astropy import time
from dateutil.parser import parse as parse_date

ENCODING = 'UTF-8'


class Field:
    """
    A data field for storing PSG configurations.

    Parameters
    ----------
    name : str
        The name of the field.
    default : any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is False.

    Attributes
    ----------
    _name : str
        The name of the field.
    _value : any
        The value of the field.
    default : any
        The default value of the field.
    null : bool
        If false, the field cannot be empty.
    """

    def __init__(self, name: str, default: Any = None, null: bool = True):
        self.default = default
        self.null = null
        self._name = name
        self._value = None

    @property
    def is_null(self) -> bool:
        """
        If the Field._value is null

        :type: bool
        """
        return self._value is None

    @property
    def name(self) -> bytes:
        """
        The parameter name of this field, formated for PSG.

        :type: bytes
        """
        return bytes(f'<{self._name.upper()}>', encoding=ENCODING)

    @property
    def value(self) -> bytes:
        """
        The value of this field.

        :type: bytes
        """
        return bytes(self._str_property, encoding=ENCODING)

    @value.setter
    def value(self, value_to_set: Any):
        """
        Setter function for ``Field._value``

        Parameters
        ----------
        value_to_set : any
            The value to set to ``self._value``

        Raises
        ------
        ValueError
            If a null value is given but not allowed.
        """
        if value_to_set is None and not self.null:
            raise ValueError("Field cannot be null.")
        self._value = value_to_set if value_to_set is not None else self.default

    @property
    def content(self) -> bytes:
        """
        The field formated as a line in a PSG config file.

        :type: bytes
        """
        if self.is_null:
            return b''
        else:
            return self.name + self.value

    @property
    def _str_property(self):
        """
        The ``Field._value`` formated as a string.

        :type: str
        """
        return str(self._value)

    def __str__(self):
        return str(self.content, encoding=ENCODING)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self._name!r}, value={self._value!r})"


class CharField(Field):
    """
    A data field representing a string of characters.

    Parameters
    ----------
    name : str
        The name of the field.
    max_length : int
        The maximum length of the string.

    Attributes
    ----------
    _name : str
        The name of the field.
    _value : any
        The value of the field.
    default : any
        The default value of the field.
    null : bool
        If false, the field cannot be empty.

    Other Parameters
    ----------------
    default : any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is False.
    """
    _value:str
    def __init__(self, name: str, default: str = None, null: bool = True, max_length: int = 255):
        super().__init__(name, default, null)
        self.max_length = max_length

    @property
    def _str_property(self):
        return str(self._value)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, str):
            raise TypeError("Value must be a string.")
        elif len(value_to_set) > self.max_length:
            raise ValueError("Value exceeds max length.")
        super(CharField, CharField).value.__set__(self, value_to_set)

class CharChoicesField(CharField):
    """
    A character string datafield with limited options.
    """
    _value:str
    def __init__(self, name: str, options:Tuple, default: str = None, null: bool = True, max_length: int = 255):
        super().__init__(name, default, null, max_length)
        self._options = options
    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        elif not any([value_to_set == option for option in self._options]):
            msg = f'Value must be one of {",".join(self._options)}.'
            raise ValueError(msg)
        super(CharField, CharField).value.__set__(self, value_to_set)


class DateField(Field):
    """
    A data field representing a date and time.
    """
    _value:time.Time
    def __init__(self, name: str, default: Any = None, null: bool = True):
        super().__init__(name, default, null)
    @property
    def _str_property(self):
        self._value:time.Time
        return self._value.strftime('%Y/%m/%d %H:%M')
    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        else:
            if isinstance(value_to_set,str):
                value_to_set = parse_date(value_to_set)
            value_to_set = time.Time(value_to_set)
        super(DateField, DateField).value.__set__(self, value_to_set)
    

class IntegerField(Field):
    """
    A data field containing an integer value.
    """
    _value:int
    @property
    def _str_property(self):
        return str(self._value)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is not None and not isinstance(value_to_set, int):
            raise TypeError("Value must be an integer.")
        super(IntegerField, IntegerField).value.__set__(self, value_to_set)


class FloatField(Field):
    """
    A data field containing a float.
    """
    _value:float
    def __init__(self, name: str, default: float = None, null: bool = True, fmt: str = '.2f'):
        super().__init__(name, default, null)
        self.fmt = fmt

    @property
    def _str_property(self):
        return f'{self._value:{self.fmt}}'

    @Field.value.setter
    def value(self, value_to_set):
        if isinstance(value_to_set, int):
            value_to_set = float(value_to_set)
        if value_to_set is not None and not isinstance(value_to_set, float):
            raise TypeError("Value must be a float.")
        super(FloatField, FloatField).value.__set__(self, value_to_set)


class QuantityField(Field):
    """
    A data field representing a quantity.
    """
    _value:u.Quantity
    def __init__(
        self,
        name: str,
        unit: u.Unit,
        default: u.Quantity = None,
        null: bool = True,
        fmt: str = '.2f'
    ):
        super().__init__(name, default, null)
        self.unit = unit
        self.fmt = fmt

    @property
    def _str_property(self):
        return f'{self._value.to_value(self.unit):{self.fmt}}'

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, u.Quantity):
            raise TypeError('Value must be a Quantity.')
        elif not value_to_set.isscalar:
            raise ValueError('QuantityField values must be a scalar, not an array.')
        elif value_to_set.unit.physical_type != self.unit.physical_type:
            msg = f'Value set is {value_to_set} ({value_to_set.unit.physical_type}). '
            msg += f'Must be of type {self.unit.physical_type}.'
            raise u.UnitConversionError(msg)
        super(QuantityField, QuantityField).value.__set__(self, value_to_set)

class CodedQuantityField(Field):
    """
    A base class for fields where PSG requires a unit to be specified.
    """
    _value:u.Quantity
    def __init__(
            self,
            allowed_units:Tuple[u.Unit],
            unit_codes:Tuple[u.Unit],
            fmt:Tuple[str] or str,
            names:Tuple[str],
            default: Any = None,
            null: bool = True
    ):
        super().__init__(None,default,null)
        self._allowed_units = allowed_units
        self._unit_codes = unit_codes
        self._fmt = fmt
        self._names = names
    @property
    def name(self):
        raise NotImplementedError('This field produces multiple lines of PSG config file.')
    @property
    def _str_property(self):
        raise NotImplementedError('This field produces multiple lines of PSG config file.')
    @property
    def is_ambiguous(self):
        physical_types = [unit.physical_type for unit in self._allowed_units]
        if len(set(physical_types)) == len(physical_types):
            return False
        else:
            return True
    @Field.value.setter
    def value(self, value_to_set:u.Quantity):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, u.Quantity):
            raise TypeError('Value must be a Quantity.')
        elif not value_to_set.isscalar:
            raise ValueError('QuantityField values must be a scalar, not an array.')
        elif not any([value_to_set.unit.physical_type == unit.physical_type for unit in self._allowed_units]):
            msg = f'Value set is {value_to_set} ({value_to_set.unit.physical_type}). '
            msg += f'Must be of types {",".join([unit.to_string() for unit in self._allowed_units])}.'
            raise u.UnitConversionError(msg)
        elif self.is_ambiguous:
            if not any([value_to_set.unit == unit for unit in self._allowed_units]):
                msg = f'Value for {self._name} is ambiguous. Please use one of these units: {",".join([unit.to_string() for unit in self._allowed_units])}'
                raise u.UnitTypeError(msg)
        super(CodedQuantityField, CodedQuantityField).value.__set__(self, value_to_set)
    @property
    def content(self):
        raise NotImplementedError('`content` method must be implemented by a subclass.')
    @property
    def _unit(self):
        if self.is_null:
            return None
        else:
            if self.is_ambiguous:
                if self._value.unit in self._allowed_units:
                    return self._value.unit
                else:
                    raise u.UnitTypeError('`self._value.unit` not in allowed units.')
            else:
                try:
                    unit = {unit.physical_type:unit for unit in self._allowed_units}[self._value.unit.physical_type]
                    return unit
                except KeyError:
                    raise u.UnitTypeError(f'Cannot find allowed unit with physical type {self._value.unit.physical_type}.')
    @property
    def _unit_code(self):
        unit_code = {unit:code for unit,code in zip(self._allowed_units,self._unit_codes)}[self._unit]
        return unit_code
    @property
    def fmt(self):
        if isinstance(self._fmt,str):
            return self._fmt
        else:
            _fmt = {unit:f for unit,f in zip(self._allowed_units,self._fmt)}[self._unit]
            return _fmt
    def _get_values(self):
        value_str = f'{self._value.to_value(self._unit):{self.fmt}}'
        return value_str, self._unit_code
    @property
    def content(self) -> bytes:
        if self.is_null:
            return b''
        else:
            name1, name2 = self._names
            value_str, unit_code = self._get_values()
            line1_str = f'<{name1.upper()}>{value_str}'
            line2_str = f'<{name2.upper()}>{unit_code}'
            return bytes(f'{line1_str}\n{line2_str}',encoding=ENCODING)

class MultiQuantityField(Field):
    """
    A data field where the interpreted unit depends on other parameters.
    """
    _value:u.Quantity
    def __init__(
        self,
        name: str,
        units: Tuple[u.Unit],
        default: u.Quantity = None,
        null: bool = True,
        fmt: str = '.2f'
    ):
        super().__init__(name, default, null)
        self._units = units
        self.fmt = fmt
    @property
    def unit(self):
        if self.is_null:
            return None
        else:
            for unit in self._units:
                if self._value.unit.physical_type == unit.physical_type:
                    return unit
            raise u.UnitTypeError(f'Corresponding unit for {self._value} not found.')
    @property
    def _str_property(self):
        return f'{self._value.to_value(self.unit):{self.fmt}}'

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, u.Quantity):
            raise TypeError('Value must be a Quantity.')
        elif not value_to_set.isscalar:
            raise ValueError('QuantityField values must be a scalar, not an array.')
        elif not any([value_to_set.unit.physical_type == unit.physical_type for unit in self._units]):
            msg = f'Value set is {value_to_set} ({value_to_set.unit.physical_type}). '
            msg += f'Must be of of one of {",".join([unit.to_string() for unit in self._units])}.'
            raise u.UnitTypeError(msg)
        super(MultiQuantityField, MultiQuantityField).value.__set__(self, value_to_set)



class GeometryOffsetField(Field):
    """
    Data field for the geometry offset.
    """
    _allowed_units:Tuple[u.Unit] = (u.Unit('arcsec'),u.Unit('arcmin'), u.deg, u.km, u.dimensionless_unscaled)
    _unit_codes:Tuple[str] = ('arcsec', 'arcmin', 'deg', 'km', 'diameter')
    fmt = '.4f'
    def __init__(
        self,
        default: u.Quantity = None,
        null: bool = True
    ):
        super().__init__('gravity', default, null)
    
    @property
    def name(self):
        raise NotImplementedError('This field produces three lines of PSG config file.')
    @property
    def _str_property(self):
        raise NotImplementedError('This field produces three lines of PSG config file.')
    def _validate(self,value:u.Quantity):
        if value is None:
            pass
        elif not isinstance(value, u.Quantity):
            if isinstance(value,(float,int)):
                value = value*u.dimensionless_unscaled
            else:
                raise TypeError('Value must be a Quantity.')
        elif not value.isscalar:
            raise ValueError('QuantityField values must be a scalar, not an array.')
        elif not any([value.unit.physical_type == unit.physical_type for unit in self._allowed_units]):
            msg = f'Value set is {value} ({value.unit.physical_type}). '
            msg += f'Must be of types {",".join([unit.to_string() for unit in self._allowed_units])}.'
            raise u.UnitConversionError(msg)
        return value
    @Field.value.setter
    def value(self, values:Tuple[u.Quantity]):
        if values is None:
            value_to_set = None
        else:
            value_ns,value_ew = values
            value_ns = self._validate(value_ns)
            value_ew = self._validate(value_ew)
            if not value_ns.unit.physical_type == value_ew.unit.physical_type:
                msg = f'EW offset cannot be {value_ew.unit} if NS offset is {value_ns.unit}.'
                raise u.UnitConversionError(msg)
            value_to_set = {'ns':value_ns,'ew':value_ew}
        super(GeometryOffsetField, GeometryOffsetField).value.__set__(self, value_to_set)
        
    def _get_values(self):
        unit_to_use = self._value['ns'].unit
        unit_code = {unit:code for unit,code in zip(self._allowed_units,self._unit_codes)}[unit_to_use]
        value_ns_str = f'{self._value["ns"].to_value(unit_to_use):{self.fmt}}'
        value_ew_str = f'{self._value["ew"].to_value(unit_to_use):{self.fmt}}'
        return value_ns_str, value_ew_str, unit_code
    @property
    def content(self) -> bytes:
        if self.is_null:
            return b''
        else:
            value_ns_str, value_ew_str, unit_code = self._get_values()
            line1_str = f'<GEOMETRY-OFFSET-NS>{value_ns_str}'
            line2_str = f'<GEOMETRY-OFFSET-EW>{value_ew_str}'
            line3_str = f'<GEOMETRY-OFFSET-UNIT>{unit_code}'
            return bytes(f'{line1_str}\n{line2_str}\n{line3_str}',encoding=ENCODING)




class Model:
    """
    A base class for data models.
    """
    def __init__(self, **kwargs):
        for field_name, field in self.__class__.__dict__.items():
            if isinstance(field, Field):
                field_value = kwargs.get(field_name, field.default)
                newfield = deepcopy(field)
                newfield.value = field_value
                self.__setattr__(field_name, newfield)

    def __setattr__(self, __name: str, __value: Any) -> None:
        attr = self.__dict__.get(__name, None)
        if isinstance(attr, Field):
            attr.value = __value
        else:
            super().__setattr__(__name, __value)
    @property
    def content(self):
        lines = []
        for _, field in self.__dict__.items():
            if isinstance(field,Field):
                if not field.is_null:
                    lines.append(field.content)
        return b'\n'.join(lines)
