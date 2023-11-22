"""
This module contains the basic functionality for fields in PSG
config objects.
"""
from typing import Any,Tuple
import warnings
from copy import deepcopy
from astropy import units as u
from astropy import time
from dateutil.parser import parse as parse_date
import numpy as np

from pypsg import units as u_psg

ENCODING = 'UTF-8'

class NullFieldComparisonError(Exception):
    pass

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
    def __eq__(self, other:'Field'):
        if not isinstance(other, Field):
            raise TypeError("Can only compare fields with other fields.")
        if not self.name == other.name:
            raise ValueError("Can only compare fields with the same name.")
        if self.is_null and other.is_null:
            return True
        if self.is_null:
            raise NullFieldComparisonError('Comparing null field to non-null field.')
        if other.is_null:
            raise NullFieldComparisonError('Comparing non-null field to null field.')
        return self.value == other.value

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
    def _read(self,d:dict):
        """
        Abstract _read method
        """
        raise NotImplementedError('Attempted to call abstract _read method from the base class.')
    def read(self,d:dict):
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that isntance.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        Any
            The information necessary to construct a class instance.
        """
        return self._read(d)
    @property
    def raw_value(self):
        return self._value


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
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            return str(d[key])
        except KeyError:
            return None

class CharChoicesField(CharField):
    """
    A character string datafield with limited options.
    """
    _value:str
    def __init__(self, name: str, options:Tuple, default: str = None, null: bool = True, max_length: int = 255):
        super().__init__(name, default, null, max_length)
        self._options = options
    @Field.value.setter
    def value(self, value_to_set:str):
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
    def value(self, value_to_set:str):
        if value_to_set is None:
            pass
        else:
            if isinstance(value_to_set,str):
                value_to_set = parse_date(value_to_set)
            value_to_set = time.Time(value_to_set)
        super(DateField, DateField).value.__set__(self, value_to_set)
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            return str(d[key])
        except KeyError:
            return None
    

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
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            return int(d[key])
        except KeyError:
            return None



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
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            return float(d[key])
        except KeyError:
            return None


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
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            return u.Quantity(float(d[key]),self.unit)
        except KeyError:
            return None

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
    # @property
    # def content(self):
    #     raise NotImplementedError('`content` method must be implemented by a subclass.')
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
    def parse_unit(self,code:str)->u.Unit:
        """
        Parse a unit code to get it's associated unit.

        Parameters
        ----------
        code : str
            The unit code given.

        Returns
        -------
        astropy.units.Unit
            The associated unit.
        """
        codes = self._unit_codes
        units = self._allowed_units
        d = {c:unit for c, unit in zip(codes,units)}
        return d[code]
    def _read(self,d:dict):
        value_key, unit_key = self._names
        value_key = value_key.upper()
        unit_key = unit_key.upper()
        try:
            value = float(d[value_key])
            code = str(d[unit_key])
            unit = self.parse_unit(code)
            return u.Quantity(value,unit)
        except KeyError:
            return None

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
    def _read(self,d:dict):
        raise NotImplementedError

class GeometryUserParamField(MultiQuantityField):
    """
    Data field for the geometry user parameters.
    """
    def __init__(
        self,
        default: u.Quantity = None,
        null: bool = True
    ):
        name = 'geometry-user-parameter'
        units = (u.deg, u.km)
        super().__init__(name, units, default, null)
    def _read(self,d:dict):
        key = self._name.upper()
        try:
            switch = str(d['GEOMETRY'])
            if switch == 'NADIR':
                unit = u.deg
            else:
                unit = u.km
            return u.Quantity(float(d[key]),unit)
        except KeyError:
            return None
    



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
        super().__init__('geometry-offset', default, null)
    
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
    def _read(self,d:dict):
        try:
            ns_value = float(d['GEOMETRY-OFFSET-NS'])
            ew_value = float(d['GEOMETRY-OFFSET-EW'])
            unit_code = str(d['GEOMETRY-OFFSET-UNIT'])
            unit = {code:unit for code,unit in zip(self._unit_codes,self._allowed_units)}[unit_code]
            return (u.Quantity(ns_value,unit),u.Quantity(ew_value,unit))
        except KeyError:
            return None
            

class Molecule:
    """
    Class to store data on individual molecules.

    Parameters
    ----------
    name : str
        The molecular identifier, e.g. `H2O` for water.
    type : str
        The profile database to use, e.g. `HIT[1]` for HITRAN water data.
    abn : astropy.units.Quantity or float or int
        The abundance of the molecule. Floats and ints will be cast to dimensionless.
    
    .. warning::
        PSG also allows the `m-3`, `molec`, `s-1`, and `tau` unit types.
        These should be implemented eventually.
    """
    _allowed_units = (u.pct,u_psg.ppmv,u_psg.ppbv,u_psg.pptv,u.Unit('m-2'),u.dimensionless_unscaled)
    _unit_codes = ('%','ppmv','ppbv','pptv','m2','scl')
    _fmt = '.2e'
    def __init__(self,name:str,type:str,abn:u.Quantity):
        self.name = name
        self.type = type
        if isinstance(abn,(int,float)):
            abn = abn*u.dimensionless_unscaled
        self._abn = abn
    @staticmethod
    def get_unit(code:str):
        try:
            return {code:unit for code,unit in zip(Molecule._unit_codes,Molecule._allowed_units)}[code]
        except KeyError:
            raise ValueError(f'Invalid unit code: {code}')
    def _validate(self):
        assert self._abn.unit in self._allowed_units
    @property
    def abn(self):
        return self._abn.to_value(self._abn.unit)
    @property
    def unit_code(self):
        return {unit:code for unit,code in zip(self._allowed_units,self._unit_codes)}[self._abn.unit]
    @property
    def fmt(self):
        return self._fmt
class Aerosol(Molecule):
    """
    Extension of the `Molecule` class for Aerosols.

    .. warning::
        PSG also allows a `wg` size unit type. This should be implemented in the future.
    """
    _allowed_size_units = (u.um,u.m,u.LogUnit(u.um),u.dimensionless_unscaled)
    _size_unit_codes = ('um','m','lum','scl')
    _fmt_size = '.2e'
    def __init__(self, name: str, type: str, abn: u.Quantity,size: u.Quantity):
        super().__init__(name, type, abn)
        if isinstance(size,(int,float)):
            size = size*u.dimensionless_unscaled
        self._size = size
        self._validate()
    @staticmethod
    def get_size_unit(code:str):
        try:
            return {code:unit for code,unit in zip(Aerosol._size_unit_codes,Aerosol._allowed_size_units)}[code]
        except KeyError:
            raise ValueError(f'Invalid unit code: {code}')
    @staticmethod
    def get_abn_unit(code:str):
        return Molecule.get_unit(code)
    
    def _validate(self):
        assert self._size.unit in self._allowed_size_units
        super()._validate()
    @property
    def size(self):
        return self._size.to_value(self._size.unit)
    @property
    def size_unit_code(self):
        return {unit:code for unit,code in zip(self._allowed_size_units,self._size_unit_codes)}[self._size.unit]
    @property
    def fmt_size(self):
        return self._fmt_size

class MoleculesField(Field):
    _value:Tuple[Molecule]
    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)
    @Field.value.setter
    def value(self, molecules:Tuple[Molecule]):
        if molecules is None:
            pass
        else:
            for molecule in molecules:
                if not isinstance(molecule,Molecule):
                    raise TypeError('MoleculeField values must be Molecule objects.')
            super(MoleculesField, MoleculesField).value.__set__(self, molecules)
    @property
    def _str_property(self):
        raise NotImplementedError('This method is not implemented.')
    @property
    def _ngas(self):
        return len(self._value)
    @property
    def ngas(self):
        return f'<ATMOSPHERE-NGAS>{self._ngas}'
    @property
    def gas(self):
        names = [mol.name for mol in self._value]
        return f'<ATMOSPHERE-GAS>{",".join(names)}'
    @property
    def type(self):
        types = [mol.type for mol in self._value]
        return f'<ATMOSPHERE-TYPE>{",".join(types)}'
    @property
    def abun(self):
        abuns = [f'{mol.abn:{mol.fmt}}' for mol in self._value]
        return f'<ATMOSPHERE-ABUN>{",".join(abuns)}'
    @property
    def unit(self):
        units = [mol.unit_code for mol in self._value]
        return f'<ATMOSPHERE-UNIT>{",".join(units)}'
    @property
    def content(self):
        s = f'{self.ngas}\n{self.gas}\n{self.type}\n{self.abun}\n{self.unit}'
        return bytes(s,encoding=ENCODING)
    def _read(self, d:dict):
        try:
            ngas = int(d['ATMOSPHERE-NGAS'])
            gases = d['ATMOSPHERE-GAS'].split(',')
            types = d['ATMOSPHERE-TYPE'].split(',')
            abuns = d['ATMOSPHERE-ABUN'].split(',')
            units = d['ATMOSPHERE-UNIT'].split(',')
        except KeyError:
            return None
        abuns = [float(abun) for abun in abuns]
        units = [Molecule.get_unit(unit) for unit in units]
        abuns = [abun*unit for abun, unit in zip(abuns,units)]
        if not len(gases) == ngas:
            raise ValueError('Incorrect number of gases in ATMOSPHERE-GAS.')
        if not len(types) == ngas:
            raise ValueError('Incorrect number of types in ATMOSPHERE-TYPE.')
        if not len(abuns) == ngas:
            raise ValueError('Incorrect number of abuns in ATMOSPHERE-ABUN.')
        if not len(units) == ngas:
            raise ValueError('Incorrect number of units in ATMOSPHERE-UNIT.')
        return tuple(Molecule(gas,type,abun) for gas,type,abun in zip(gases,types,abuns))

class AerosolsField(Field):
    _value:Tuple[Aerosol]
    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)
    @Field.value.setter
    def value(self, aerosols:Tuple[Aerosol]):
        if aerosols is None:
            pass
        else:
            for aerosol in aerosols:
                if not isinstance(aerosol,Aerosol):
                    raise TypeError('AerosolsField values must be Aerosol objects.')
            super(AerosolsField, AerosolsField).value.__set__(self, aerosols)
    @property
    def _str_property(self):
        raise NotImplementedError('This method is not implemented.')
    @property
    def _naero(self):
        return len(self._value)
    @property
    def naero(self):
        return f'<ATMOSPHERE-NAERO>{self._naero}'
    @property
    def aeros(self):
        names = [aero.name for aero in self._value]
        return f'<ATMOSPHERE-AEROS>{",".join(names)}'
    @property
    def type(self):
        types = [aero.type for aero in self._value]
        return f'<ATMOSPHERE-ATYPE>{",".join(types)}'
    @property
    def abun(self):
        abuns = [f'{aero.abn:{aero.fmt}}' for aero in self._value]
        return f'<ATMOSPHERE-AABUN>{",".join(abuns)}'
    @property
    def unit(self):
        units = [aero.unit_code for aero in self._value]
        return f'<ATMOSPHERE-AUNIT>{",".join(units)}'
    @property
    def size(self):
        sizes = [f'{aero.size:{aero.fmt}}' for aero in self._value]
        return f'<ATMOSPHERE-ASIZE>{",".join(sizes)}'
    @property
    def size_unit(self):
        units = [aero.size_unit_code for aero in self._value]
        return f'<ATMOSPHERE-ASUNI>{",".join(units)}'
    @property
    def content(self):
        s = f'{self.naero}\n{self.aeros}\n{self.type}\n{self.abun}\n{self.unit}\n{self.size}\n{self.size_unit}'
        return bytes(s,encoding=ENCODING)
    def _read(self,d:dict):
        try:
            naero = int(d['ATMOSPHERE-NAERO'])
            aeros = d['ATMOSPHERE-AEROS'].split(',')
            types = d['ATMOSPHERE-ATYPE'].split(',')
            abuns = d['ATMOSPHERE-AABUN'].split(',')
            units = d['ATMOSPHERE-AUNIT'].split(',')
            sizes = d['ATMOSPHERE-ASIZE'].split(',')
            size_units = d['ATMOSPHERE-ASUNI'].split(',')
        except KeyError:
            return None
        if not len(aeros) == naero:
            raise ValueError('Incorrect number of aerosols in ATMOSPHERE-AEROS.')
        if not len(types) == naero:
            raise ValueError('Incorrect number of types in ATMOSPHERE-ATYPE.')
        if not len(abuns) == naero:
            raise ValueError('Incorrect number of abuns in ATMOSPHERE-AABUN.')
        if not len(units) == naero:
            raise ValueError('Incorrect number of units in ATMOSPHERE-AUNIT.')
        if not len(sizes) == naero:
            raise ValueError('Incorrect number of sizes in ATMOSPHERE-ASIZE.')
        if not len(size_units) == naero:
            raise ValueError('Incorrect number of size units in ATMOSPHERE-ASUNI.')

        abuns = [float(abun) for abun in abuns]
        sizes = [float(size) for size in sizes]
        units = [Aerosol.get_abn_unit(unit) for unit in units]
        size_units = [Aerosol.get_size_unit(unit) for unit in size_units]
        return tuple(Aerosol(aero,type,abun*unit,size*size_unit) for aero,type,abun,unit,size,size_unit in zip(aeros,types,abuns,units,sizes,size_units))

class Profile:
    """
    A data container for an atmospheric profile.
    """
    PRESSURE = 'PRESSURE'
    TEMPERATURE = 'TEMPERATURE'
    def __init__(self,name:str,dat:np.ndarray,unit:u.Unit = u.dimensionless_unscaled):
        self.name = name
        self._dat = dat
        self.unit = unit
        self._validate()
    def _validate(self):
        if not self._dat.ndim == 1:
            raise ValueError('dat must have a shape of 1.')
    @property
    def dat(self):
        return self._dat*self.unit
    @property
    def nlayers(self):
        return self._dat.shape[0]
    def fget_layer(self,i:int):
        return self._dat[i]
    def get_layer(self,i:int):
        return self.fget_layer(i)*self.unit
    @property
    def is_temperature(self):
        return self.unit.physical_type == u.K.physical_type
    @property
    def is_pressure(self):
        return self.unit.physical_type == u.bar.physical_type
    @staticmethod
    def get_unit(name:str):
        if name == Profile.PRESSURE:
            return u.bar
        elif name == Profile.TEMPERATURE:
            return u.K
        else:
            return u.dimensionless_unscaled

class ProfileField(Field):
    _value:Tuple[Profile]
    _fmt = '.6e'
    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)
    
    @Field.value.setter
    def value(self, profiles:Tuple[Profile]):
        if profiles is None:
            pass
        else:
            for profile in profiles:
                if not isinstance(profile,Profile):
                    raise TypeError('ProfileField values must be Profile objects.')
            nlayers = {profile.nlayers for profile in profiles}
            if not len(nlayers) == 1:
                raise ValueError('Profiles must all have the same shape.')
            is_temp = [profile.is_temperature for profile in profiles]
            if not np.sum(is_temp) == 1:
                raise ValueError(f'ProfileField recieved {np.sum(is_temp)} temperature profiles!')
            is_press = [profile.is_pressure for profile in profiles]
            if not np.sum(is_press) == 1:
                raise ValueError(f'ProfileField recieved {np.sum(is_press)} pressure profiles!')
            super(ProfileField, ProfileField).value.__set__(self, profiles)
    
    def get_molecules(self,i:int):
        return [profile.fget_layer(i) for profile in self._value if not (profile.is_pressure or profile.is_temperature)]
    def get_temperature(self,i:int):
        return [profile.fget_layer(i) for profile in self._value if profile.is_temperature][0]
    def get_pressure(self,i:int):
        return [profile.fget_layer(i) for profile in self._value if profile.is_pressure][0]
    @property
    def names(self):
        _names = [profile.name for profile in self._value if not (profile.is_pressure or profile.is_temperature)]
        return f'<ATMOSPHERE-LAYERS-MOLECULES>{",".join(_names)}'
    @property
    def nlayers(self):
        return self._value[0].nlayers
    @property
    def fmt(self):
        return self._fmt
    @property
    def str_nlayers(self):
        return f'<ATMOSPHERE-LAYERS>{self.nlayers}'
    def get_layer(self,i):
        values = [self.get_pressure(i)] + [self.get_temperature(i)] + self.get_molecules(i)
        return f'<ATMOSPHERE-LAYER-{i+1}>{",".join([f"{value:{self.fmt}}" for value in values])}'
    @property
    def content(self):
        lines = [self.names] + [self.str_nlayers] + [self.get_layer(i) for i in range(self.nlayers)]
        return bytes('\n'.join(lines), encoding=ENCODING)
    def _read(self, d: dict):
        try:
            molecules = d['ATMOSPHERE-LAYERS-MOLECULES'].split(',')
            n_layers = int(d['ATMOSPHERE-LAYERS'])
        except KeyError:
            return None
        layers:np.ndarray = np.array([
            np.fromstring(d[f'ATMOSPHERE-LAYER-{i+1}'],sep=',') for i in range(n_layers)
        ])
        profiles = []
        names = [Profile.PRESSURE, Profile.TEMPERATURE] + molecules
        for i, name in enumerate(names):
            dat = layers[:,i]
            unit = Profile.get_unit(name)
            profiles.append(Profile(name,dat,unit))
        return tuple(profiles)

class BooleanField(Field):
    _value:bool
    def __init__(self, name: str, default: Any = None, null: bool = True, true:str = 'Y', false:str = 'N'):
        super().__init__(name, default, null)
        self._true = true
        self._false = false

    @property
    def _str_property(self):
        return self._true if self._value else self._false

    @Field.value.setter
    def value(self, value_to_set:bool):
        if value_to_set is not None and not isinstance(value_to_set, bool):
            raise TypeError("Value must be boolean.")
        super(BooleanField, BooleanField).value.__set__(self, value_to_set)
    def _read(self, d: dict):
        key = self._name.upper()
        try:
            value = str(d[key])
        except KeyError:
            return None
        if value == self._true:
            return True
        elif value == self._false:
            return False
        else:
            raise ValueError(f'Value must be one of {self._true} or {self._false}.')


    







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
    # @staticmethod
    def _type_to_create(self,*args,**kwargs):
        return self.__class__
    
    @classmethod
    def from_cfg(cls,cfg:dict):
        """
        Construct a Model instance from a config dict.
        """
        initialized = cls() # we must first initialize an instance
                            # so that we have access to the fields
        cls = initialized._type_to_create(cfg=cfg)
        kwargs = {}
        for field_name, field in cls.__dict__.items():
            if isinstance(field, Field):
                kwargs[field_name] = field.read(cfg)
        return cls(**kwargs)
                

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
    @property
    def keys(self)->dict:
        """
        Get the keys of a Model, formated
        for PSG as {'attr_name':'PSG_name'}.

        :type:dict
        """
        keys = {}
        for key, value in self.__dict__.items():
            if isinstance(value,Field):
                value:Field
                keys[key] = value.name
        return keys
    @property
    def fields(self)->dict:
        """
        Get the fields of a Model.

        :type:list
        """
        return {name:field for name,field in self.__dict__.items() if isinstance(field,Field)}
    
    def __eq__(self, other):
        if not isinstance(other, Model):
            raise TypeError("Can only compare models with other models.")
        return self.content == other.content
    def compare_to(self,other,strict=False,warn=True):
        """
        Compare a model to another. The other model is optionally
        allowed to contain extra fields that are not in the current model.
        This is because PSG sometimes adds fields internally that are
        not set by the user.
        
        Parameters
        ----------
        other : Model
            The model to compare to
        strict : bool
            If True, raise an error if the other model contains extra fields.
        warn : bool
            If True, warn if the other model contains extra fields.
        
        Returns
        -------
        bool
            True if the models are equal.
        """
        if not isinstance(other, Model):
            raise TypeError("Can only compare models with other models.")
        
        other_fields = other.fields
        self_fields = self.fields
        if not all(key1==key2 for key1,key2 in zip(self_fields.keys(),other_fields.keys())):
            raise ValueError("Can only compare models with the same fields.")
        # make sure the other model has all the fields.
        keys = self_fields.keys()
        should_warn = False
        for key in keys:
            sf:Field = self_fields[key]
            of:Field = other_fields[key]
            try:
                if not sf == of:
                    return False
            except NullFieldComparisonError: # one is null
                if sf.is_null: # self is null
                    return False
                else: # other is null
                    if strict:
                        return False
                    if warn:
                        should_warn = True
        if should_warn:
            warnings.warn(f"Model {other.__class__.__name__} has extra field {key}.",RuntimeWarning)
        return True
            
