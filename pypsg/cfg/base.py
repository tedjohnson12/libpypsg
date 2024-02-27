"""
CFG Base
~~~~~~~~

This module contains the basic functionality for fields in PSG
config objects.
"""
from typing import Any, Tuple, List
import warnings
from copy import deepcopy
from astropy import units as u
from astropy import time
from dateutil.parser import parse as parse_date
import numpy as np
from abc import ABC, abstractmethod

from pypsg import units as u_psg

ENCODING = 'UTF-8'


class NullFieldComparisonError(Exception):
    """
    Exception raised when comparing a null field to a non-null field.
    """


class Table:
    """
    A python representation of a PSG datatable.

    Parameters
    ----------
    x : np.ndarray | u.Quantity
        The x values.
    y : np.ndarray | u.Quantity
        The y values.

    Raises
    ------
    ValueError
        If x and y do not have the same length.

    Attributes
    ----------
    x : np.ndarray | u.Quantity
        The x values.
    y : np.ndarray | u.Quantity
        The y values.

    Examples
    --------
    >>> t = Table(np.array([1,2,3]),np.array([4,5,6]))
    >>> t.to_string()
    '4.00@1.00,5.00@2.00,6.00@3.00'
    """

    def __init__(
        self,
        x: np.ndarray | u.Quantity,
        y: np.ndarray | u.Quantity,
    ):
        if not len(x) == len(y):
            raise ValueError('x and y must have the same length')
        self.x = x
        self.y = y

    def to_string(self, xunit: u.Unit = None, yunit: u.Unit = None, fmt='.2e'):
        """
        Format the table as a string.

        Parameters
        ----------
        xunit : u.Unit, optional
            The unit of the x values. Defaults to None.
        yunit : u.Unit, optional
            The unit of the y values. Defaults to None.
        fmt : str, optional
            The format string. Defaults to '.2e'.

        Returns
        -------
        str
            The table as a string. This is the format that PSG expects.

        Raises
        ------
        TypeError
            If x or y are quantities and the corresponding unit is None.

        Examples
        --------
        >>> t = Table(np.array([1,2,3]),np.array([4,5,6]))
        >>> t.to_string()
        '4.00@1.00,5.00@2.00,6.00@3.00'
        """
        x, y = self.x, self.y
        if xunit is not None:
            x = x.to_value(xunit)
        if yunit is not None:
            y = y.to_value(yunit)
        if isinstance(x, u.Quantity):
            raise TypeError('x must be a numpy array')
        if isinstance(y, u.Quantity):
            raise TypeError('y must be a numpy array')
        return ','.join([f'{_y:{fmt}}@{_x:{fmt}}' for _x, _y in zip(x, y)])

    @staticmethod
    def read(dat: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Read a string representation of a table.

        Parameters
        ----------
        dat : str
            The string representation of the table.

        Returns
        -------
        np.ndarray
            The x values.
        np.ndarray
            The y values.

        Notes
        -----
        The purpose of this method is to read a table from a
        config file and format it to be initialized by a field.
        """
        pairs = dat.split(',')
        y = [float(pair.split('@')[0]) for pair in pairs]
        x = [float(pair.split('@')[1]) for pair in pairs]
        return np.array(x), np.array(y)

    def __eq__(self, other: 'Table'):
        if not isinstance(other, Table):
            raise TypeError('other must be a Table')
        return np.all(self.x == other.x) and np.all(self.y == other.y)


class Field(ABC):
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

    def __eq__(self, other: 'Field'):
        if not isinstance(other, Field):
            raise TypeError("Can only compare fields with other fields.")
        if not self.name == other.name:
            raise ValueError("Can only compare fields with the same name.")
        if self.is_null and other.is_null:
            return True
        if self.is_null:
            raise NullFieldComparisonError(
                'Comparing null field to non-null field.')
        if other.is_null:
            raise NullFieldComparisonError(
                'Comparing non-null field to null field.')
        return self.value == other.value

    @property
    def name(self) -> bytes:
        """
        The parameter name of this field, formated for PSG.

        :type: bytes
        """
        return bytes(f'<{self._name.upper()}>', encoding=ENCODING)

    @property
    def asbytes(self) -> bytes:
        """
        The value of this field.

        :type: bytes
        """
        return bytes(self._str_property, encoding=ENCODING)
    @property
    def value(self):
        """
        Get the raw value of the field

        :type: Any
        """
        return self._value
    @value.setter
    @abstractmethod
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
    def content(self) -> asbytes:
        """
        The field formated as a line in a PSG config file.

        :type: bytes
        """
        if self.is_null:
            return b''
        else:
            return self.name + self.asbytes

    @property
    @abstractmethod
    def _str_property(self):
        """
        The ``Field._value`` formated as a string.

        :type: str
        """
        raise NotImplementedError(
            'Attempted to call abstract _str_property method from the base class.')

    def __str__(self):
        return str(self.content, encoding=ENCODING)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self._name!r}, value={self._value!r})"
    
    @abstractmethod
    def read(self, d: dict):
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
        raise NotImplementedError(
            'Attempted to call abstract _read method from the base class.')

    


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
    _value: str

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

    def read(self, d: dict)->str:
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that instance.
        
        If the desired field is not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        str
            The information necessary to construct a class instance.
        
        """
        key = self._name.upper()
        if key in d:
            return str(d[key])
        else:
            return None


class CharChoicesField(CharField):
    """
    A character string datafield with limited options.
    
    Parameters
    ----------
    name : str
        The name of the field.
    options : Tuple of str
        The options for the field.
    default : str, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    max_length : int
        The maximum length of the string.
    """
    _value: str

    def __init__(
        self,
        name: str,
        options: Tuple[str],
        default: str = None,
        null: bool = True,
        max_length: int = 255
    ):
        super().__init__(name, default, null, max_length)
        self._options = options

    @Field.value.setter
    def value(self, value_to_set: str):
        if value_to_set is None:
            pass
        elif not any([value_to_set == option for option in self._options]):
            msg = f'Value must be one of {",".join(self._options)}. Got {value_to_set}'
            raise ValueError(msg)
        super(CharField, CharField).value.__set__(self, value_to_set)

class UnitChoicesField(Field):
    def __init__(
        self,
        name: str,
        options: Tuple[u.Unit, ...],
        codes: Tuple[str, ...],
        default: str = None,
        null: bool = True,
    ):
        super().__init__(name, default, null)
        self._options = options
        self._codes = codes
    @property
    def _code(self):
        return {unit:code for unit,code in zip(self._options,self._codes)}[self._value]
    @property
    def _str_property(self):
        return self._code
    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, (u.Unit,u.CompositeUnit)):
            raise TypeError(f"Value must be a unit. Instead got {type(value_to_set)}")
        elif value_to_set not in self._options:
            msg = f'Value must be one of {",".join([unit.to_string() for unit in self._options])}.'
            raise u.UnitTypeError(msg)
        super(UnitChoicesField, UnitChoicesField).value.__set__(self, value_to_set)
    def read(self,d:dict)->u.Unit:
        key = self._name.upper()
        decoder = {code:unit for unit,code in zip(self._options,self._codes)}
        try:
            return u.Unit(decoder[d[key]])
        except KeyError:
            return None

    
    


class DateField(Field):
    """
    A data field representing a date and time.
    """
    _value: time.Time
    @property
    def _str_property(self):
        self._value: time.Time
        return self._value.strftime('%Y/%m/%d %H:%M')

    @Field.value.setter
    def value(self, value_to_set: str):
        if value_to_set is None:
            pass
        else:
            if isinstance(value_to_set, str):
                value_to_set = parse_date(value_to_set)
            value_to_set = time.Time(value_to_set)
        super(DateField, DateField).value.__set__(self, value_to_set)

    def read(self, d: dict)->str:
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that instance.
        
        If the desired field is not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        str
            The information necessary to construct an instance of DateField.
        """
        key = self._name.upper()
        try:
            return str(d[key])
        except KeyError:
            return None


class IntegerField(Field):
    """
    A data field containing an integer value.
    """
    _value: int
    @property
    def _str_property(self):
        return str(self._value)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is not None and not isinstance(value_to_set, int):
            raise TypeError("Value must be an integer.")
        super(IntegerField, IntegerField).value.__set__(self, value_to_set)

    def read(self, d: dict):
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that instance.
        
        If the desired field is not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        str
            The information necessary to construct an instance of IntegerField.
        """
        key = self._name.upper()
        try:
            return int(d[key])
        except KeyError:
            return None


class FloatField(Field):
    """
    A data field containing a float.

    Parameters
    ----------
    name : str
        The name of the field.
    default : float, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    fmt : str, optional
        The format string for the float. Default is '.2f'.
    allow_table : bool, optional
        Whether the field can be set to a Table. Defaults to False.
    xunit : u.Unit, optional
        The unit of the x values for a Table. Defaults to None.
    yunit : u.Unit, optional
        The unit of the y values for a Table. Defaults to None.

    Raises
    ------
    ValueError
        If allow_table is False and xunit and yunit are not None.

    """
    _value: float | Table

    def __init__(
        self,
        name: str,
        default: float = None,
        null: bool = True,
        fmt: str = '.2f',
        allow_table: bool = False,
        xunit: u.Unit = None,
        yunit: u.Unit = None,
    ):
        super().__init__(name, default, null)
        self.fmt = fmt
        if not allow_table and (xunit is not None) or (yunit is not None):
            raise ValueError(
                'If allow_table is False, xunit and yunit must be None.')
        self.allow_table = allow_table
        self.xunit = xunit
        self.yunit = yunit

    @property
    def is_table(self) -> bool:
        """
        True if the value is a Table.

        :type: bool
        """
        return isinstance(self._value, Table)

    @property
    def _str_property(self):
        if self.is_table:
            return self._value.to_string(self.xunit, self.yunit, self.fmt)
        else:
            return f'{self._value:{self.fmt}}'

    def _check_table(self, table: Table):
        """
        Checks for Table input.
        """
        if not self.allow_table:
            msg = f'Table values are not allowed for field `{self._name}`.'
            raise TypeError(msg)
        if self.xunit is None:
            if isinstance(table.x, u.Quantity):
                msg = f'Field `{self._name}` requires table x values to be numpy arrays.'
                raise TypeError(msg)
        else:  # xunit is some unit
            if not isinstance(table.x, u.Quantity):
                msg = f'Field `{self._name}` requires table x values to be astropy quantities.'
                raise TypeError(msg)
            if not self.xunit.physical_type == table.x.unit.physical_type:
                msg = f'Field `{self._name}` requires table x values to be of type {self.xunit.physical_type}.'
                raise u.UnitConversionError(msg)
        if self.yunit is None:
            if isinstance(table.y, u.Quantity):
                msg = f'Field `{self._name}` requires table y values to be numpy arrays.'
                raise TypeError(msg)
        else:  # yunit is some unit
            if not isinstance(table.y, u.Quantity):
                msg = f'Field `{self._name}` requires table y values to be astropy quantities.'
                raise TypeError(msg)
            if not self.yunit.physical_type == table.y.unit.physical_type:
                msg = f'Field `{self._name}` requires table y values to be of type {self.yunit.physical_type}.'
                raise u.UnitConversionError(msg)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        else:
            if isinstance(value_to_set, Table):
                self._check_table(value_to_set)
            else:
                if isinstance(value_to_set, int):
                    value_to_set = float(value_to_set)
                if value_to_set is not None and not isinstance(value_to_set, float):
                    raise TypeError("Value must be a float.")
        super(FloatField, FloatField).value.__set__(self, value_to_set)

    def read(self, d: dict)->float | Table:
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that instance.
        
        If the desired field is not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        float | Table
            The information necessary to construct an instance of FloatField.
        """
        key = self._name.upper()
        try:
            return float(d[key])
        except ValueError:
            x, y = Table.read(d[key])
            if self.xunit is not None:
                x = x*self.xunit
            if self.yunit is not None:
                y = y*self.yunit
            return Table(x, y)
        except KeyError:
            return None


class QuantityField(Field):
    """
    A data field representing a quantity.

    Parameters
    ----------
    name : str
        The name of the field.
    unit : u.Unit
        The unit of the quantity.
    default : u.Quantity, optional
        The default value of the field. Defaults to None.
    null : bool, optional
        Whether the field can be set to None. Defaults to True.
    fmt : str, optional
        The format string for the quantity. Defaults to '.2f'.
    allow_table : bool, optional
        Whether the field can be set to a Table. Defaults to False.
    xunit : u.Unit, optional
        The unit of the x values for a Table. Defaults to None.
    yunit : u.Unit, optional
        The unit of the y values for a Table. Defaults to None.

    Raises
    ------
    ValueError
        If allow_table is False and xunit and yunit are not None.

    """
    _value: u.Quantity | Table

    def __init__(
        self,
        name: str,
        unit: u.Unit,
        default: u.Quantity = None,
        null: bool = True,
        fmt: str = '.2f',
        allow_table: bool = False,
        xunit: u.Unit = None,
        yunit: u.Unit = None,
    ):
        super().__init__(name, default, null)
        self.unit = unit
        self.fmt = fmt
        if (allow_table is False) and ((xunit is not None) or (yunit is not None)):
            raise ValueError(
                f'allow_table is {allow_table}, xunit and yunit must be None.')
        self.allow_table = allow_table
        self.xunit = xunit
        self.yunit = yunit

    @property
    def is_table(self) -> bool:
        """
        True if the value is a Table.

        :type: bool
        """
        return isinstance(self._value, Table)

    @property
    def _str_property(self):
        if self.is_table:
            return self._value.to_string(self.xunit, self.yunit, self.fmt)
        else:
            return f'{self._value.to_value(self.unit):{self.fmt}}'

    def _check_table(self, table: Table):
        """
        Checks for Table input
        """
        if not self.allow_table:
            msg = f'Table values are not allowed for field `{self._name}`.'
            raise TypeError(msg)
        if self.xunit is None:
            if isinstance(table.x, u.Quantity):
                msg = f'Field `{self._name}` requires table x values to be numpy arrays.'
                raise TypeError(msg)
        else:  # xunit is some unit
            if not isinstance(table.x, u.Quantity):
                msg = f'Field `{self._name}` requires table x values to be astropy quantities.'
                raise TypeError(msg)
            if not self.xunit.physical_type == table.x.unit.physical_type:
                msg = f'Field `{self._name}` requires table x values to be of type {self.xunit.physical_type}.'
                raise u.UnitConversionError(msg)
        if self.yunit is None:
            if isinstance(table.y, u.Quantity):
                msg = f'Field `{self._name}` requires table y values to be numpy arrays.'
                raise TypeError(msg)
        else:  # yunit is some unit
            if not isinstance(table.y, u.Quantity):
                msg = f'Field `{self._name}` requires table y values to be astropy quantities.'
                raise TypeError(msg)
            if not self.yunit.physical_type == table.y.unit.physical_type:
                msg = f'Field `{self._name}` requires table y values to be of type {self.yunit.physical_type}.'
                raise u.UnitConversionError(msg)

    def _check_quantity(self, value: u.Quantity):
        """
        Checks for Quantity input
        """
        if not value.isscalar:
            raise ValueError(
                'QuantityField values must be a scalar, not an array.')
        if value.unit.physical_type != self.unit.physical_type:
            msg = f'Value set is {value} ({value.unit.physical_type}). '
            msg += f'Must be of type {self.unit.physical_type}.'
            raise u.UnitConversionError(msg)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is None:
            pass
        else:
            if isinstance(value_to_set, Table):
                self._check_table(value_to_set)
            elif isinstance(value_to_set, u.Quantity):
                self._check_quantity(value_to_set)
            else:
                raise TypeError('Value must be a Quantity or BaseTable.')
        super(QuantityField, QuantityField).value.__set__(self, value_to_set)

    def read(self, d: dict)->u.Quantity | Table:
        """
        Read a dictionary and return the information necessary to construct
        a QuantityField instance.
        
        If the desired field is not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        u.Quantity | Table
            The information necessary to construct an instance of QuantityField.
        """
        key = self._name.upper()
        try:
            return u.Quantity(float(d[key]), self.unit)
        except ValueError:
            x, y = Table.read(d[key])
            if self.xunit is not None:
                x = x*self.xunit
            if self.yunit is not None:
                y = y*self.yunit
            return Table(x, y)
        except KeyError:
            return None


class CodedQuantityField(Field):
    """
    A quantity field where PSG requires the unit be specified.
    
    Parameters
    ----------
    allowed_units : tuple
        The allowed units.
    unit_codes : tuple
        The allowed unit codes.
    fmt : str
        The format string.
    names : tuple
        The names of the field.
    default : astropy.units.Quantity, optional
        The default value. Default is None.
    """
    _value: u.Quantity

    def __init__(
            self,
            allowed_units: Tuple[u.Unit, ...],
            unit_codes: Tuple[u.Unit, ...],
            fmt: Tuple[str, ...] or str,
            names: Tuple[str, ...],
            default: u.Quantity = None,
            null: bool = True
    ):
        super().__init__(None, default, null)
        self._allowed_units = allowed_units
        self._unit_codes = unit_codes
        self._fmt = fmt
        self._names = names

    @property
    def name(self):
        raise NotImplementedError(
            'This field produces multiple lines of PSG config file.')

    @property
    def _str_property(self):
        raise NotImplementedError(
            'This field produces multiple lines of PSG config file.')

    @property
    def is_ambiguous(self) -> bool:
        """
        True of the unit physical types are not unique.

        :type: bool
        """
        physical_types = [unit.physical_type for unit in self._allowed_units]
        if len(set(physical_types)) == len(physical_types):
            return False
        else:
            return True

    @Field.value.setter
    def value(self, value_to_set: u.Quantity):
        if value_to_set is None:
            pass
        elif not isinstance(value_to_set, u.Quantity):
            raise TypeError('Value must be a Quantity.')
        elif not value_to_set.isscalar:
            raise ValueError(
                'QuantityField values must be a scalar, not an array.')
        elif not any([value_to_set.unit.physical_type == unit.physical_type for unit in self._allowed_units]):
            msg = f'Value set is {value_to_set} ({value_to_set.unit.physical_type}). '
            units = ",".join([unit.to_string()
                             for unit in self._allowed_units])
            msg += f'Must be of types {units}.'
            raise u.UnitConversionError(msg)
        elif self.is_ambiguous:
            if not any([value_to_set.unit == unit for unit in self._allowed_units]):
                units = ",".join([unit.to_string()
                                 for unit in self._allowed_units])
                msg = f'Value for {self._name} is ambiguous. Please use one of these units: {units}'
                raise u.UnitTypeError(msg)
        super(CodedQuantityField, CodedQuantityField).value.__set__(
            self, value_to_set)

    @property
    def _unit(self):
        if self.is_null:
            return None
        else:
            if self.is_ambiguous:
                if self._value.unit in self._allowed_units:
                    return self._value.unit
                else:
                    raise u.UnitTypeError(
                        '`self._value.unit` not in allowed units.')
            else:
                try:
                    unit = {unit.physical_type: unit for unit in self._allowed_units}[
                        self._value.unit.physical_type]
                    return unit
                except KeyError as e:
                    raise u.UnitTypeError(
                        f'Cannot find allowed unit with physical type {self._value.unit.physical_type}.', e)

    @property
    def _unit_code(self):
        unit_code = {unit: code for unit, code in zip(
            self._allowed_units, self._unit_codes)}[self._unit]
        return unit_code

    @property
    def fmt(self) -> str:
        """
        The string format for the value.

        :type: str
        """
        if isinstance(self._fmt, str):
            return self._fmt
        else:
            _fmt = {unit: f for unit, f in zip(self._allowed_units, self._fmt)}[
                self._unit]
            return _fmt

    def _get_values(self) -> Tuple[str, str]:
        """
        PSG readable strings for the value and unit code.
        """
        value_str = f'{self._value.to_value(self._unit):{self.fmt}}'
        return value_str, self._unit_code

    @property
    def content(self) -> bytes:
        if self.is_null:
            return b''
        else:
            name1, name2 = self._names
            name1: str
            name2: str
            value_str, unit_code = self._get_values()
            line1_str = f'<{name1.upper()}>{value_str}'
            line2_str = f'<{name2.upper()}>{unit_code}'
            return bytes(f'{line1_str}\n{line2_str}', encoding=ENCODING)

    def parse_unit(self, code: str) -> u.Unit:
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
        d = {c: unit for c, unit in zip(codes, units)}
        return d[code]

    def read(self, d: dict)->u.Quantity:
        """
        Read a dictionary and return the information necessary to construct
        a CodedQuantityField instance.
        
        If the desired fields are not in the dictionary, return None (i.e. the field is null)
        
        Parameters
        ----------
        d : dict
            The dictionary to read.
        
        Returns
        -------
        astropy.units.Quantity
            The quantity read from the dictionary.
        """
        value_key, unit_key = self._names
        value_key = value_key.upper()
        unit_key = unit_key.upper()
        try:
            value = float(d[value_key])
            code = str(d[unit_key])
            unit = self.parse_unit(code)
            return u.Quantity(value, unit)
        except KeyError:
            return None


class GeometryOffsetField(Field):
    """
    Data field for the geometry offset.
    
    Parameters
    ----------
    default : astropy.units.Quantity
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    
    .. todo::
        This should be replaced by a more general `TupleQuantityField`.
    """
    _allowed_units: Tuple[u.Unit] = (u.Unit('arcsec'), u.Unit(
        'arcmin'), u.deg, u.km, u.dimensionless_unscaled)
    _unit_codes: Tuple[str] = ('arcsec', 'arcmin', 'deg', 'km', 'diameter')
    fmt = '.4f'

    def __init__(
        self,
        default: u.Quantity = None,
        null: bool = True
    ):
        super().__init__('geometry-offset', default, null)

    @property
    def name(self):
        raise NotImplementedError(
            'This field produces three lines of PSG config file.')

    @property
    def _str_property(self):
        raise NotImplementedError(
            'This field produces three lines of PSG config file.')

    def _validate(self, value: u.Quantity):
        if value is None:
            pass
        elif not isinstance(value, u.Quantity):
            if isinstance(value, (float, int)):
                value = value*u.dimensionless_unscaled
            else:
                raise TypeError('Value must be a Quantity.')
        elif not value.isscalar:
            raise ValueError(
                'QuantityField values must be a scalar, not an array.')
        elif not any([value.unit.physical_type == unit.physical_type for unit in self._allowed_units]):
            msg = f'Value set is {value} ({value.unit.physical_type}). '
            msg += f'Must be of types {",".join([unit.to_string() for unit in self._allowed_units])}.'
            raise u.UnitConversionError(msg)
        return value

    @Field.value.setter
    def value(self, values: Tuple[u.Quantity]):
        if values is None:
            value_to_set = None
        else:
            value_ns, value_ew = values
            value_ns = self._validate(value_ns)
            value_ew = self._validate(value_ew)
            if not value_ns.unit.physical_type == value_ew.unit.physical_type:
                msg = f'EW offset cannot be {value_ew.unit} if NS offset is {value_ns.unit}.'
                raise u.UnitConversionError(msg)
            value_to_set = {'ns': value_ns, 'ew': value_ew}
        super(GeometryOffsetField, GeometryOffsetField).value.__set__(
            self, value_to_set)

    def _get_values(self):
        unit_to_use = self._value['ns'].unit
        unit_code = {unit: code for unit, code in zip(
            self._allowed_units, self._unit_codes)}[unit_to_use]
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
            return bytes(f'{line1_str}\n{line2_str}\n{line3_str}', encoding=ENCODING)

    def read(self, d: dict)-> Tuple[u.Quantity, u.Quantity]:
        """
        Read a dictionary and return the information necessary to construct
        a GeometryOffsetField instance.
        
        If the dictionary does not contain the necessary keys, return None.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        Tuple of astropy.units.Quantity
            The NS and EW offsets.
        """
        try:
            ns_value = float(d['GEOMETRY-OFFSET-NS'])
            ew_value = float(d['GEOMETRY-OFFSET-EW'])
            unit_code = str(d['GEOMETRY-OFFSET-UNIT'])
            unit = {code: unit for code, unit in zip(
                self._unit_codes, self._allowed_units)}[unit_code]
            return (u.Quantity(ns_value, unit), u.Quantity(ew_value, unit))
        except KeyError:
            return None


class Molecule:
    """
    Class to store data on individual molecules.

    Parameters
    ----------
    name : str
        The molecular identifier, e.g. `H2O` for water.
    database : str
        The profile database to use, e.g. `HIT[1]` for HITRAN water data.
    abn : astropy.units.Quantity or float or int
        The abundance of the molecule. Floats and ints will be cast to dimensionless.

    .. warning::
        PSG also allows the `m-3`, `molec`, `s-1`, and `tau` unit types.
        These should be implemented eventually.
    """
    _allowed_units = (u.pct, u_psg.ppm, u_psg.ppb, u_psg.ppt,
                      u.Unit('m-2'), u.dimensionless_unscaled)
    _unit_codes = ('%', 'ppmv', 'ppbv', 'pptv', 'm2', 'scl')
    _fmt = '.2e'

    def __init__(
        self,
        name: str,
        database: str,
        abn: u.Quantity
    ):
        self.name = name
        self.database = database
        if isinstance(abn, (int, float)):
            abn = abn*u.dimensionless_unscaled
        self._abn = abn

    @staticmethod
    def get_abn_unit(code: str) -> u.Unit:
        """
        Get the unit for a given unit code.

        :type: unit
        """
        try:
            return {code: unit for code, unit in zip(Molecule._unit_codes, Molecule._allowed_units)}[code]
        except KeyError as e:
            raise ValueError(f'Invalid unit code: {code}', e) from e

    def _validate(self):
        assert self._abn.unit in self._allowed_units

    @property
    def abn(self) -> float:
        """
        The abundance of the molecule.

        :type: float
        """
        return self._abn.to_value(self._abn.unit)

    @property
    def unit_code(self) -> str:
        """
        The unit code of the molecule.

        :type: str
        """
        return {unit: code for unit, code in zip(self._allowed_units, self._unit_codes)}[self._abn.unit]

    @property
    def fmt(self) -> str:
        """
        The string format for the value.

        :type: str
        """
        return self._fmt


class Aerosol(Molecule):
    """
    Extension of the `Molecule` class for Aerosols.
    
    Parameters
    ----------
    name : str
        The aerosol identifier, e.g. `Water` for water.
    database : str
        The profile database to use.
    abn : astropy.units.Quantity
        The abundance of the aerosol.
    size : astropy.units.Quantity
        The size of the aerosol.

    .. warning::
        PSG also allows a `wg` size unit type. This should be implemented in the future.
    """
    _allowed_size_units = (u.um, u.m, u.LogUnit(u.um),
                           u.dimensionless_unscaled)
    _size_unit_codes = ('um', 'm', 'lum', 'scl')
    _fmt_size = '.2e'

    def __init__(
        self,
        name: str,
        database: str,
        abn: u.Quantity,
        size: u.Quantity
    ):
        super().__init__(name, database, abn)
        if isinstance(size, (int, float)):
            size = size*u.dimensionless_unscaled
        self._size = size
        self._validate()

    @staticmethod
    def get_size_unit(code: str):
        """
        Get the unit for a given unit code.

        Parameters
        ----------
        code : str
            The unit code.

        Returns
        -------
        astropy.units.Unit
            The associated unit.

        Raises
        ------
        ValueError
            If the unit code is not valid.
        """
        try:
            return {code: unit for code, unit in zip(Aerosol._size_unit_codes, Aerosol._allowed_size_units)}[code]
        except KeyError as e:
            raise ValueError(f'Invalid unit code: {code}', e) from e

    @staticmethod
    def get_abn_unit(code: str):
        """
        Get the unit for a given unit code.

        Parameters
        ----------
        code : str
            The unit code.

        Returns
        -------
        astropy.units.Unit
            The associated unit.
        """
        return Molecule.get_abn_unit(code)

    def _validate(self):
        assert self._size.unit in self._allowed_size_units
        super()._validate()

    @property
    def size(self) -> float:
        """
        The size of the aerosol.

        :type: float
        """
        return self._size.to_value(self._size.unit)

    @property
    def size_unit_code(self) -> str:
        """
        The unit code of the aerosol size.

        :type: str
        """
        return {unit: code for unit, code in zip(self._allowed_size_units, self._size_unit_codes)}[self._size.unit]

    @property
    def fmt_size(self) -> str:
        """
        The string format for the size.

        :type: str
        """
        return self._fmt_size


class MoleculesField(Field):
    """
    A Field to store molecular data.

    Parameters
    ----------
    default : Any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    """
    _value: Tuple[Molecule]

    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)

    @Field.value.setter
    def value(self, molecules: Tuple[Molecule]):
        if molecules is None:
            pass
        else:
            for molecule in molecules:
                if not isinstance(molecule, Molecule):
                    raise TypeError(
                        'MoleculeField values must be Molecule objects.')
            super(MoleculesField, MoleculesField).value.__set__(self, molecules)

    @property
    def _str_property(self):
        raise NotImplementedError('This method is not implemented.')

    @property
    def _ngas(self) -> int:
        return len(self._value)

    @property
    def ngas(self) -> str:
        """
        The number of molecules in string format.

        :type: str
        """
        return f'<ATMOSPHERE-NGAS>{self._ngas}'

    @property
    def gas(self) -> str:
        """
        The list of molecules in string format.

        :type: str
        """
        names = [mol.name for mol in self._value]
        return f'<ATMOSPHERE-GAS>{",".join(names)}'

    @property
    def type(self) -> str:
        """
        The list of molecule types in string format.

        :type: str
        """
        types = [mol.database for mol in self._value]
        return f'<ATMOSPHERE-TYPE>{",".join(types)}'

    @property
    def abun(self) -> str:
        """
        The list of molecule abundances in string format.

        :type: str
        """
        abuns = [f'{mol.abn:{mol.fmt}}' for mol in self._value]
        return f'<ATMOSPHERE-ABUN>{",".join(abuns)}'

    @property
    def unit(self) -> str:
        """
        The list of molecule units in string format.

        :type: str
        """
        units = [mol.unit_code for mol in self._value]
        return f'<ATMOSPHERE-UNIT>{",".join(units)}'

    @property
    def content(self):
        s = f'{self.ngas}\n{self.gas}\n{self.type}\n{self.abun}\n{self.unit}'
        return bytes(s, encoding=ENCODING)

    def read(self, d: dict)-> Tuple[Molecule]:
        """
        Read the data from a dictionary.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        tuple of Molecule
            A tuple of Molecule objects.
        
        Raises
        ------
        ValueError
            If the number of molecules in the dictionary is incorrect.
        """
        try:
            ngas = int(d['ATMOSPHERE-NGAS'])
            gases = d['ATMOSPHERE-GAS'].split(',')
            types = d['ATMOSPHERE-TYPE'].split(',')
            abuns = d['ATMOSPHERE-ABUN'].split(',')
            units = d['ATMOSPHERE-UNIT'].split(',')
        except KeyError:
            return None
        abuns = [float(abun) for abun in abuns]
        units = [Molecule.get_abn_unit(unit) for unit in units]
        abuns = [abun*unit for abun, unit in zip(abuns, units)]
        if not len(gases) == ngas:
            raise ValueError('Incorrect number of gases in ATMOSPHERE-GAS.')
        if not len(types) == ngas:
            raise ValueError('Incorrect number of types in ATMOSPHERE-TYPE.')
        if not len(abuns) == ngas:
            raise ValueError('Incorrect number of abuns in ATMOSPHERE-ABUN.')
        if not len(units) == ngas:
            raise ValueError('Incorrect number of units in ATMOSPHERE-UNIT.')
        return tuple(Molecule(gas, type, abun) for gas, type, abun in zip(gases, types, abuns))


class AerosolsField(Field):
    """
    A Field to store aerosol data.

    Parameters
    ----------
    default : Any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    """
    _value: Tuple[Aerosol]

    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)

    @Field.value.setter
    def value(self, aerosols: Tuple[Aerosol]):
        if aerosols is None:
            pass
        else:
            for aerosol in aerosols:
                if not isinstance(aerosol, Aerosol):
                    raise TypeError(
                        'AerosolsField values must be Aerosol objects.')
            super(AerosolsField, AerosolsField).value.__set__(self, aerosols)

    @property
    def _str_property(self):
        raise NotImplementedError('This method is not implemented.')

    @property
    def _naero(self) -> int:
        return len(self._value)

    @property
    def naero(self) -> str:
        """
        The number of aerosols in str format.

        :type: str
        """
        return f'<ATMOSPHERE-NAERO>{self._naero}'

    @property
    def aeros(self) -> str:
        """
        The list of aerosol names in string format.

        :type: str
        """
        names = [aero.name for aero in self._value]
        return f'<ATMOSPHERE-AEROS>{",".join(names)}'

    @property
    def type(self) -> str:
        """
        The list of aerosol types in string format.

        :type: str
        """
        types = [aero.database for aero in self._value]
        return f'<ATMOSPHERE-ATYPE>{",".join(types)}'

    @property
    def abun(self) -> str:
        """
        The list of aerosol abundances in string format.

        :type: str
        """
        abuns = [f'{aero.abn:{aero.fmt}}' for aero in self._value]
        return f'<ATMOSPHERE-AABUN>{",".join(abuns)}'

    @property
    def unit(self) -> str:
        """
        The list of aerosol units in string format.

        :type: str
        """
        units = [aero.unit_code for aero in self._value]
        return f'<ATMOSPHERE-AUNIT>{",".join(units)}'

    @property
    def size(self) -> str:
        """
        The list of aerosol sizes in string format.

        :type: str
        """
        sizes = [f'{aero.size:{aero.fmt}}' for aero in self._value]
        return f'<ATMOSPHERE-ASIZE>{",".join(sizes)}'

    @property
    def size_unit(self) -> str:
        """
        The list of aerosol size units in string format.

        :type: str
        """
        units = [aero.size_unit_code for aero in self._value]
        return f'<ATMOSPHERE-ASUNI>{",".join(units)}'

    @property
    def content(self):
        if self._naero == 0:
            return bytes('', encoding=ENCODING)
        s = f'{self.naero}\n{self.aeros}\n{self.type}\n{self.abun}\n{self.unit}\n{self.size}\n{self.size_unit}'
        return bytes(s, encoding=ENCODING)

    def read(self, d: dict)-> Tuple[Aerosol]:
        """
        Read the data from the dictionary.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        Tuple[Aerosol]
            A tuple of Aerosol objects.
        
        Raises
        ------
        ValueError
            If the dictionary gives conflicting information.
        """
        try:
            def parse_empty(l:list):
                """
                Ensure that `''.split()` returns an empty list.
                """
                if len(l) == 1:
                    if l[0] == '':
                        return []
                return l
            naero = int(d['ATMOSPHERE-NAERO'])
            aeros = parse_empty(d['ATMOSPHERE-AEROS'].split(','))
            types = parse_empty(d['ATMOSPHERE-ATYPE'].split(','))
            abuns = parse_empty(d['ATMOSPHERE-AABUN'].split(','))
            units = parse_empty(d['ATMOSPHERE-AUNIT'].split(','))
            sizes = parse_empty(d['ATMOSPHERE-ASIZE'].split(','))
            size_units = parse_empty(d['ATMOSPHERE-ASUNI'].split(','))
        except KeyError:
            return None
        if not len(aeros) == naero:
            raise ValueError(
                'Incorrect number of aerosols in ATMOSPHERE-AEROS.')
        if not len(types) == naero:
            raise ValueError('Incorrect number of types in ATMOSPHERE-ATYPE.')
        if not len(abuns) == naero:
            raise ValueError('Incorrect number of abuns in ATMOSPHERE-AABUN.')
        if not len(units) == naero:
            raise ValueError('Incorrect number of units in ATMOSPHERE-AUNIT.')
        if not len(sizes) == naero:
            raise ValueError('Incorrect number of sizes in ATMOSPHERE-ASIZE.')
        if not len(size_units) == naero:
            raise ValueError(
                'Incorrect number of size units in ATMOSPHERE-ASUNI.')

        abuns = [float(abun) for abun in abuns]
        sizes = [float(size) for size in sizes]
        units = [Aerosol.get_abn_unit(unit) for unit in units]
        size_units = [Aerosol.get_size_unit(unit) for unit in size_units]
        return tuple(Aerosol(aero, type, abun*unit, size*size_unit) for aero, type, abun, unit, size, size_unit in zip(aeros, types, abuns, units, sizes, size_units))


class Profile:
    """
    A data container for an atmospheric profile.

    Parameters
    ----------
    name : str
        The name of the profile.
    dat : np.ndarray, shape=(nlayers, )
        The data.
    unit : astropy.units.Unit
        The unit of the data.
    """
    PRESSURE = 'PRESSURE'
    TEMPERATURE = 'TEMPERATURE'

    def __init__(self, name: str, dat: np.ndarray, unit: u.Unit = u.dimensionless_unscaled):
        self.name = name
        if isinstance(dat, u.Quantity):
            raise TypeError('dat must be a numpy array.')
        self._dat = dat
        self.unit = unit
        self._validate()

    def _validate(self):
        if not self._dat.ndim == 1:
            raise ValueError('dat must have a shape of 1.')

    @property
    def dat(self) -> u.Quantity:
        """
        The data as a Quantity.

        :type: astropy.units.Quantity
        """
        return self._dat*self.unit

    @property
    def nlayers(self) -> int:
        """
        The number of layers.
        """
        return self._dat.shape[0]

    def fget_layer(self, i: int) -> float:
        """
        The value at a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        float
            The value at the layer.
        """
        return self._dat[i]

    def get_layer(self, i: int) -> u.Quantity:
        """
        Get the value at a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        astropy.units.Quantity
            The value at the layer.
        """
        return self.fget_layer(i)*self.unit

    @property
    def is_temperature(self) -> bool:
        """
        True if the profile is temperature.

        :type: bool
        """
        return self.unit.physical_type == u.K.physical_type

    @property
    def is_pressure(self) -> bool:
        """
        True if the profile is pressure.

        :type: bool
        """
        return self.unit.physical_type == u.bar.physical_type

    @staticmethod
    def get_unit(name: str) -> u.Unit:
        """
        The the unit for a given profile name.

        Parameters
        ----------
        name : str
            The profile name.

        Returns
        -------
        astropy.units.Unit
            The profile unit.
        """
        if name == Profile.PRESSURE:
            return u.bar
        elif name == Profile.TEMPERATURE:
            return u.K
        else:
            return u.dimensionless_unscaled


class ProfileField(Field):
    """
    A field to store profiles.

    Parameters
    ----------
    default : Any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    """
    _value: Tuple[Profile]
    _fmt = '.6e'

    def __init__(self, default: Any = None, null: bool = True):
        super().__init__(None, default, null)

    @Field.value.setter
    def value(self, profiles: Tuple[Profile]):
        if profiles is None:
            pass
        else:
            for profile in profiles:
                if not isinstance(profile, Profile):
                    raise TypeError(
                        'ProfileField values must be Profile objects.')
            nlayers = {profile.nlayers for profile in profiles}
            if not len(nlayers) == 1:
                raise ValueError('Profiles must all have the same shape.')
            is_temp = [profile.is_temperature for profile in profiles]
            if np.sum(is_temp) != 1:
                raise ValueError(
                    f'ProfileField recieved {np.sum(is_temp)} temperature profiles!')
            is_press = [profile.is_pressure for profile in profiles]
            if np.sum(is_press) != 1:
                raise ValueError(
                    f'ProfileField recieved {np.sum(is_press)} pressure profiles!')
            super(ProfileField, ProfileField).value.__set__(self, profiles)

    def get_molecules(self, i: int) -> List[float]:
        """
        Get the abundances of the molecules at a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        List[float]
            The abundances of the molecules.
        """
        return [profile.fget_layer(i) for profile in self._value if not (profile.is_pressure or profile.is_temperature)]

    def get_temperature(self, i: int) -> float:
        """
        Get the temperature at a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        float
            The temperature.
        """
        return [profile.fget_layer(i) for profile in self._value if profile.is_temperature][0]

    def get_pressure(self, i: int) -> float:
        """
        Get the pressure at a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        float
            The pressure.
        """
        return [profile.fget_layer(i) for profile in self._value if profile.is_pressure][0]

    @property
    def names(self) -> str:
        """
        The list of layer names in string format.

        :type: str
        """
        _names = [profile.name for profile in self._value if not (
            profile.is_pressure or profile.is_temperature)]
        return f'<ATMOSPHERE-LAYERS-MOLECULES>{",".join(_names)}'

    @property
    def nlayers(self) -> int:
        """
        The number of layers.

        :type: int
        """
        return self._value[0].nlayers

    @property
    def fmt(self) -> str:
        """
        The string format to use.

        :type: str
        """
        return self._fmt

    @property
    def str_nlayers(self) -> str:
        """
        The string representation of the number of layers.

        :type: str
        """
        return f'<ATMOSPHERE-LAYERS>{self.nlayers}'

    def get_layer(self, i) -> str:
        """
        The string representation of a layer.

        Parameters
        ----------
        i : int
            The layer index.

        Returns
        -------
        str
            The string representation of the layer.
        """
        values = [self.get_pressure(
            i)] + [self.get_temperature(i)] + self.get_molecules(i)
        return f'<ATMOSPHERE-LAYER-{i+1}>{",".join([f"{value:{self.fmt}}" for value in values])}'

    @property
    def content(self):
        lines = [self.names] + [self.str_nlayers] + \
            [self.get_layer(i) for i in range(self.nlayers)]
        return bytes('\n'.join(lines), encoding=ENCODING)
    
    @property
    def _str_property(self):
        raise NotImplementedError('This method is not defined for this class')

    def read(self, d: dict)->Tuple[Profile]:
        """
        Read the field from a dictionary.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        Tuple[Profile]
            The profiles read from the dictionary.
        """
        try:
            molecules = d['ATMOSPHERE-LAYERS-MOLECULES'].split(',')
            n_layers = int(d['ATMOSPHERE-LAYERS'])
        except KeyError:
            return None
        layers: np.ndarray = np.array([
            np.fromstring(d[f'ATMOSPHERE-LAYER-{i+1}'], sep=',') for i in range(n_layers)
        ])
        profiles = []
        names = [Profile.PRESSURE, Profile.TEMPERATURE] + molecules
        for i, name in enumerate(names):
            dat = layers[:, i]
            unit = Profile.get_unit(name)
            profiles.append(Profile(name, dat, unit))
        return tuple(profiles)


class BooleanField(Field):
    """
    A Field to store boolean data.

    Parameters
    ----------
    name : str
        The name of the field.
    default : any, optional
        The default value of the field. Default is None.
    null : bool, optional
        If false, the field cannot be empty. Default is True.
    true : str or list of str
        The string representation of true. Default is ['Y', 'YES'].
    false : str or list of str
        The string representation of false. Default is ['N', 'NO'].
    
    Notes
    -----
    As of `v0.2.0`, a list of strings is allowed as the true and false values.
    However, only the zeroth element will ever be passed to the `content` method.
    The other values, however, allow the program to catch aliases of the true and
    false codes.
    """
    _value: bool

    def __init__(
        self,
        name: str,
        default: Any = None,
        null: bool = True,
        true: str | List[str] = ['Y', 'YES'],
        false: str | List[str] = ['N', 'NO']
    ):
        super().__init__(name, default, null)
        self._true = true
        self._false = false

    @property
    def _str_property(self):
        value = self._true if self._value else self._false
        if isinstance(value, list):
            value = value[0]
        return value
    @Field.value.setter
    def value(self, value_to_set: bool):
        if value_to_set is not None and not isinstance(value_to_set, bool):
            raise TypeError("Value must be boolean.")
        super(BooleanField, BooleanField).value.__set__(self, value_to_set)

    def read(self, d: dict)->bool | None:
        """
        Read a dictionary and return the information necessary to
        construct a class instance. Does not construct that instance.
        
        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        
        Returns
        -------
        bool
            The information necessary to construct an instance of BooleanField.
        """
        key = self._name.upper()
        try:
            value = str(d[key])
        except KeyError:
            return None
        match self._true:
            case str():
                if value == self._true:
                    return True
            case list():
                if value in self._true:
                    return True
        match self._false:
            case str():
                if value == self._false:
                    return False
            case list():
                if value in self._false:
                    return False
        raise ValueError(
            f'Value must be one of {self._true} or {self._false}, found {value}.'
        )


class Model(ABC):
    """
    A base class for data models.

    Parameters
    ----------
    **kwargs
        The keyword arguments to initialize the fields.
    """

    def __init__(self, **kwargs):
        field_names = dir(self)
        for field_name in field_names:
            if not field_name == 'content':
                field = getattr(self, field_name)
                if isinstance(field, Field):
                    field_value = kwargs.get(field_name, field.default)
                    newfield = deepcopy(field)
                    newfield.value = field_value
                    self.__setattr__(field_name, newfield)
    # pylint: disable-next=unused-argument
    def _type_to_create(self, *args, **kwargs):
        return self.__class__

    @classmethod
    def from_cfg(cls, cfg: dict)-> 'Model':
        """
        Construct a Model instance from a config dict.

        Parameters
        ----------
        cfg : dict
            The config dict.
        """
        initialized = cls()  # we must first initialize an instance
        # so that we have access to the fields

        cls_to_create = initialized._type_to_create(cfg=cfg)
        kwargs = {}
        field_names = dir(cls_to_create)
        for field_name in field_names:
            if not field_name == 'content':
                field = getattr(cls_to_create, field_name)
                if isinstance(field, Field):
                    kwargs[field_name] = field.read(cfg)
        return cls_to_create(**kwargs)

    def __setattr__(self, __name: str, __value: Any) -> None:
        attr = self.__dict__.get(__name, None)
        if isinstance(attr, Field):
            attr.value = __value
        else:
            super().__setattr__(__name, __value)

    @property
    def content(self) -> bytes:
        """
        The model formatted as a PSG-readable bytes string.

        :type: bytes
        """
        lines = []
        field_names = dir(self)
        for field_name in field_names:
            if not field_name == 'content':
                field = getattr(self, field_name)
                if isinstance(field, Field):
                    if not field.is_null:
                        lines.append(field.content)
        return b'\n'.join(lines)

    @property
    def fields(self) -> dict:
        """
        Get the fields of a Model.

        :type:list
        """
        return {name: field for name, field in self.__dict__.items() if isinstance(field, Field)}

    def __eq__(self, other):
        if not isinstance(other, Model):
            raise TypeError("Can only compare models with other models.")
        return self.content == other.content

    def compare_to(self, other, strict=False, warn=True):
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
        if not all(key1 == key2 for key1, key2 in zip(self_fields.keys(), other_fields.keys())):
            raise ValueError("Can only compare models with the same fields.")
        # make sure the other model has all the fields.
        keys = self_fields.keys()
        should_warn = False
        extra_keys = []
        for key in keys:
            sf: Field = self_fields[key]
            of: Field = other_fields[key]
            try:
                if not sf == of:
                    return False
            except NullFieldComparisonError:  # one is null
                if sf.is_null:  # self is null
                    return False
                else:  # other is null
                    if strict:
                        return False
                    if warn:
                        extra_keys.append(key)
                        should_warn = True
        if should_warn:
            warnings.warn(
                f"Model {other.__class__.__name__} has extra field(s) {extra_keys}.", RuntimeWarning)
        return True
