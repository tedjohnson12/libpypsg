"""
This module contains the basic functionality for fields in PSG
config objects.
"""
from typing import Any
from copy import deepcopy
from astropy import units as u

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

    def __init__(self, name: str, default: Any = None, null: bool = False):
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

    def __init__(self, name: str, default: str = None, null: bool = False, max_length: int = 255):
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


class IntegerField(Field):
    """
    A data field containing an integer value.
    """
    @property
    def _str_property(self):
        return str(self._value)

    @Field.value.setter
    def value(self, value_to_set):
        if value_to_set is not None and not isinstance(value_to_set, int):
            raise TypeError("Value must be an integer.")
        super(CharField, CharField).value.__set__(self, value_to_set)


class FloatField(Field):
    """
    A data field containing a float.
    """

    def __init__(self, name: str, default: float = None, null: bool = False, fmt: str = '.2f'):
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
        super(CharField, CharField).value.__set__(self, value_to_set)


class QuantityField(Field):
    """
    A data field representing a quantity
    """

    def __init__(
        self,
        name: str,
        unit: u.Unit,
        default: u.Quantity = None,
        null: bool = False,
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
        elif value_to_set.unit.physical_type != self.unit.physical_type:
            msg = f'Value set is {value_to_set} ({value_to_set.unit.physical_type}). '
            msg += f'Must be of type {self.unit.physical_type}.'
            raise u.UnitConversionError(msg)
        super(CharField, CharField).value.__set__(self, value_to_set)


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
