"""
PyPSG Requests
--------------

Direct access to the PSG API
"""
from typing import Union, Dict
import re
import requests

from pypsg.cfg import PyConfig, BinConfig
from pypsg import settings
from pypsg.rad import PyRad
from pypsg.lyr import PyLyr

typedict: Dict[bytes, Union[PyConfig, PyRad, PyLyr]] = {
    b'cfg': PyConfig,
    b'rad': PyRad,
    b'lyr': PyLyr,
    b'noi': PyRad
}


class PSGResponse:
    """
    A class to parse the response from the PSG API.
    
    Parameters
    ----------
    cfg : PyConfig
        The PSG .cfg file.
    rad : PyRad
        The PSG .rad file.
    lyr : PyLyr
        The PSG .lyr file.
    noi : PyRad
        The PSG .noi file.
    """
    def __init__(
        self,
        cfg: PyConfig = None,
        rad: PyRad = None,
        lyr: PyLyr = None,
        noi: PyRad = None
    ):
        self.cfg = cfg
        self.rad = rad
        self.lyr = lyr
        self.noi = noi

    @classmethod
    def from_bytes(cls, b: bytes):
        """
        Read the response from PSG as a byte string.
        
        Parameters
        ----------
        b : bytes
            The response from the PSG. This is the returned file read as bytes.
        """
        pattern = rb'results_([\w]+).txt'
        split_text = re.split(pattern, b)
        names = split_text[1::2]
        content = split_text[2::2]
        data = {}
        for name, dat in zip(names, content):
            data[name] = dat.strip()
        kwargs = {}
        for key, value in typedict.items():
            value: PyConfig | PyRad | PyLyr
            if key in data:
                kwargs[key.decode(settings.get_setting('encoding'))] = value.from_bytes(data[key])
        return cls(**kwargs)
    @classmethod
    def null(cls):
        return cls()


class APICall:
    """
    A class to call the PSG API.

    Parameters
    ----------
    cfg : Config
        The PSG configuration.
    output_type : str or None
        The type of output to ask for.
    app : str or None
        The app to use.
    url : str
        The URL to send the request to.

    Attributes
    ----------
    cfg : Config
        The PSG configuration.
    output_type : str or None
        The type of output to ask for.
    app : str or None
        The app to use.
    url : str
        The URL to send the request to.
    """

    def __init__(
        self,
        cfg: Union[BinConfig, PyConfig],
        output_type: str = None,
        app: str = None,
        url: str = None
    ):
        self.cfg = cfg
        self._type = output_type
        self.app = app
        self.url = url
        if self.url is None:
            self.url = settings.get_setting('url')
        self._validate()

    def _validate(self):
        """
        Validate a class instance.

        Raises
        ------
        TypeError
            If self.cfg is not a Config object.
        TypeError
            If self.type is not a string or None.
        TypeError
            If self.app is not a string or None.
        TypeError
            If self.url is not a string.
        """
        if not isinstance(self.cfg, (PyConfig, BinConfig)):
            raise TypeError(
                'apiCall.cfg must be a PyConfig or BinaryConfig object')
        if not (isinstance(self._type, str) or self._type is None):
            if not isinstance(self._type, (list, tuple)):
                raise TypeError('apiCall.type must be a string or None')
            else:
                raise NotImplementedError('Multiple types not implemented. If you know how to do this please open an issue.')
                # for t in self._type:
                #     if not isinstance(t, str):
                #         raise TypeError('apiCall.type must be a string or None')
        if not (isinstance(self.app, str) or self.app is None):
            raise TypeError('apiCall.app must be a string or None')
        if not isinstance(self.url, str):
            raise TypeError('apiCall.url must be a string')

    @property
    def is_single_file(self):
        """
        True if only a single file is expected back from the PSG API.
        
        Returns
        -------
        bool
            True if only a single file is expected back from the PSG API.
        """
        if isinstance(self._type, (tuple, list)):
            return False
        if self._type == 'all':
            return False
        return True
    @property
    def type(self):
        """
        The type of output to ask for.

        :type: str
        """
        if isinstance(self._type,str):
            return self._type
        else:
            return ','.join(self._type)

    def __call__(self) -> PSGResponse:
        """
        Call the PSG API

        Returns
        -------
        bytes
            The reply from PSG.
        """
        data = dict(file=self.cfg.content)
        if self.type is not None:
            data['type'] = self.type
        if self.app is not None:
            data['app'] = self.app
        api_key = settings.get_setting('api_key')
        if api_key is not None:
            data['key'] = api_key
        url = self.url
        if '/api.php' not in url:
            url = f'{url}/api.php'
        reply = requests.post(
            url=url,
            data=data,
            timeout=settings.REQUEST_TIMEOUT
        )
        if reply.status_code != 200:
            raise requests.exceptions.HTTPError(reply.content)
        if self._type in ['upd', 'set']:
            return PSGResponse.null()
        elif not self.is_single_file:
            return PSGResponse.from_bytes(reply.content)
        else:
            returntype = typedict[self._type.encode(settings.get_setting('encoding'))]
            return PSGResponse(**{self._type:returntype.from_bytes(reply.content)})
