"""
A module to handle configuration files
"""

from astropy import units as u
from typing import Dict
from copy import deepcopy

from pypsg.resources.units import CFG_UNITS

ENCODING = 'UTF-8'

class Param:
    _encoding = ENCODING
    _name = ''
    value = b''
    @property
    def name(self)->bytes:
        """
        The name of the parameter formated for PSG

        Returns
        -------
        bytes
            The name of the parameter like `<NAME>`
        """
        return bytes(f'<{self._name.upper()}>', encoding=self._encoding)
    @property
    def content(self)->bytes:
        """
        The content of the parameter formated
        as a line in a PSG config file.

        Returns
        -------
        bytes
            The line of the config file as a bytes object.
        """
        return self.name + self.value
    def __hash__(self):
        return self.name.__hash__()


class StringParam(Param):
    def __init__(self,name:str, value:str):
        self._name = name
        if not isinstance(value,str):
            raise TypeError('The value of a StringParam must be a string.')
        self._value = value
    @property
    def value(self)->bytes:
        """
        The value of the StringParam

        Returns
        -------
        bytes
            The value of the parameter.
        """
        return bytes(self._value, encoding=self._encoding)

class QuantityParam(Param):
    _encoding = ENCODING
    def __init__(self,name:str,value:u.Quantity):
        self._name = name
        if not isinstance(value,u.Quantity):
            raise TypeError('The value of a QuantityParam must be a Quantity.')
        self._value = value
        try:
            self._unit = u.Unit(CFG_UNITS[name.upper()]['unit'])
            self._fmt = CFG_UNITS[name.upper()].get('fmt','.2e')
        except KeyError as err:
            if name.upper() not in CFG_UNITS:
                msg = f'{name} not found in list of known units. Double check that this parameter is a Quantity.'
                raise KeyError(msg)
            else:
                msg = f'PLEASE REPORT THIS BUG. {name} was found in the list of known units, but is perhaps formatted incorrectly.'
                msg = msg + '\nOriginal Error: ' + str(err)
                raise KeyError(msg)
        if not self._unit.physical_type == self._value.unit.physical_type:
            msg = f'Value given has physical type {self._value.unit.physical_type}, but {self._unit.physical_type} is expected.'
            raise u.UnitConversionError(msg)
    @property
    def value(self):
        return bytes(f'{self._value.to_value(self._unit):{self._fmt}}',encoding=self._encoding)
    


class Config:
    """
    A representation of a PSG config file.
    
    Parameters
    ----------
    **params : Param
        The parameters of this configuration.
    
    Attributes
    ----------
    params : dict
        The parameters of the configuration. The keys are the parameter
        names.
    """
    _encoding = ENCODING
    def __init__(self,*params:Param):
        for param in params:
            assert isinstance(param,Param)
        self.params = set(params)
    def set(self,param:Param):
        """
        Set the value of a parameter.

        Parameters
        ----------
        param : Param
            The parameter to set.
        """
        self.params.add(param)
    def remove(self,name:str or bytes):
        """
        Remove a parameter from the configuration.

        Parameters
        ----------
        name : str or bytes
            The name of the parameter to remove. If a string is used, it
            is converted in the same way as the ``Params.name`` property.
            That is ``'object'-->'<OBJECT>'``.

        Raises
        ------
        NameError
            If no parameter is found with the specified name.
        """
        if isinstance(name,str):
            name = bytes(f'<{name.upper()}>',encoding=self._encoding)
        for param in self.params:
            if param.__hash__() == name.__hash__():
                param_to_remove = param
                break
        try:
            self.params.remove(param_to_remove)
        except NameError:
            msg = f'No parameters with name {name} found.'
            raise NameError(msg)
    @property
    def content(self)->bytes:
        """
        The content of the config file.

        Returns
        -------
        bytes
            The config file as a bytes object.
        """
        params = list(self.params)
        params.sort(key=lambda x : x.name)
        return b'\n'.join([param.content for param in params])