"""
PyPSG Requests
--------------

Direct access to the PSG API
"""
import warnings
from typing import Union, Dict
import re
import requests
import logging

from pypsg.cfg import PyConfig, BinConfig
from pypsg import settings
from pypsg import exceptions
from pypsg.rad import PyRad
from pypsg.lyr import PyLyr
from pypsg.trn import PyTrn
from pypsg import docker

docker.set_url_and_run()

typedict: Dict[bytes, Union[PyConfig, PyRad, PyLyr]] = {
    b'cfg': PyConfig,
    b'rad': PyRad,
    b'lyr': PyLyr,
    b'noi': PyRad,
    b'trn': PyTrn
}

def parse_exceptions(content:bytes):
    
    content = re.sub(b'<BINARY>.*</BINARY>',b'',content)
    content = content.replace(b'\r',b'')
    content = str(content,encoding=settings.get_setting('encoding'))
    
    exception_dict = {
        'GlobES': exceptions.GlobESError,
        'PUMAS': exceptions.PUMASError
    }
    warning_dict = {
        'GENERATOR': exceptions.GeneratorWarning,
        'PUMAS': exceptions.PUMASWarning
    }
    
    matchs = re.findall(r'WARNING \| ([\w]+) \| (.*)', content)
    psg_warnings = [
        warning_dict.get(match[0], exceptions.UnknownPSGWarning)(match[1]) for match in matchs
    ]
    for warning in psg_warnings:
        warnings.warn(warning)
    
    
    matchs = re.findall(r'ERROR \| ([\w]+) \| (.*)', content)
    if len(matchs) == 0:
        return None
    errors = [
        exception_dict.get(match[0], exceptions.UnknownPSGError)(match[1]) for match in matchs
    ]
    if len(errors) == 1:
        raise errors[0]
    raise exceptions.PSGMultiError(errors)

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
    trn : PyTrn
        The PSG .trn file.
    """
    def __init__(
        self,
        cfg: PyConfig = None,
        rad: PyRad = None,
        lyr: PyLyr = None,
        noi: PyRad = None,
        trn: PyTrn = None
    ):
        self.cfg = cfg
        self.rad = rad
        self.lyr = lyr
        self.noi = noi
        self.trn = trn

    @classmethod
    def from_bytes(cls, b: bytes):
        """
        Read the response from PSG as a byte string.
        
        Parameters
        ----------
        b : bytes
            The response from the PSG. This is the returned file read as bytes.
        """
        b = b.replace(b'\r',b'')
        pattern = rb'results_([\w]+).txt'
        split_text = re.split(pattern, b)
        names = split_text[1::2]
        content = split_text[2::2]
        data = {}
        for name, dat in zip(names, content):
            data[name] = dat.strip()
        kwargs = {}
        for key, value in typedict.items():
            value: PyConfig | PyRad | PyLyr | PyTrn
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
        url: str = None,
        logger: logging.Logger = None
    ):
        self.cfg = cfg
        self._type = output_type
        self.app = app
        self.url = url
        if self.url is None:
            self.url = settings.get_setting('url')
        self.logger = logger
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
        match self._type:
            case None:
                return None
            case str():
                return self._type
            case _:
                try:
                    return ','.join(self._type)
                except TypeError as err:
                    msg = f'APICall output type must be None, a string or a list of strings. Got {self._type}.'
                    raise TypeError(msg) from err
    @staticmethod
    def call(
        cfg: Union[BinConfig, PyConfig],
        output_type: str | None,
        app: str | None,
        api_key: str | None,
        url: str,
        header: dict,
        timeout: float = 30
    )->requests.Response:
        """
        Call the PSG API and return the raw response.

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

        Returns
        -------
        requests.Response
            The reply from PSG.
        """
        data = dict(file=cfg.content)
        if output_type is not None:
            data['type'] = output_type
        if app is not None:
            data['app'] = app
        if api_key is not None:
            data['key'] = api_key
        reply: requests.Response = requests.post(
            url=url,
            data=data,
            timeout=timeout,
            headers=header
        )
        return reply
    
    def reset(self):
        """
        Reset PSG to its initial state.
        """
        api_key = settings.get_setting('api_key')
        url = self.url
        if '/api.php' not in url:
            url = f'{url}/api.php'
        _ = self.call(
            cfg=PyConfig(),
            output_type='set',
            app=None,
            api_key=api_key,
            url=url,
            header=settings.get_setting('header'),
            timeout=settings.get_setting('timeout')
        )

    def __call__(self) -> PSGResponse:
        """
        Call the PSG API

        Returns
        -------
        bytes
            The reply from PSG.
        """
        api_key = settings.get_setting('api_key')
        url = self.url
        if '/api.php' not in url:
            url = f'{url}/api.php'
        
        reply = self.call(
            cfg=self.cfg,
            output_type=self.type,
            app=self.app,
            api_key=api_key,
            url=url,
            header=settings.get_setting('header'),
            timeout=settings.get_setting('timeout')
        )
        if self.logger is not None:
            def format_content(content,title):
                if b'<BINARY>' in content:
                    content = content.split(b'<BINARY>')[0] + b'<BINARY>...</BINARY>'  + content.split(b'</BINARY>')[1]
                s = '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n' \
                    + f'{title}:\n' \
                    + str(content, encoding=settings.get_setting('encoding')) \
                        + '\n' + '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                return s
            self.logger.debug(format_content(self.cfg.content,f'Sent to {self.url} (app: {self.app}) with mode `{self.type}`'))
            self.logger.debug(format_content(reply.content, 'Received from PSG'))
        try:
            reply.raise_for_status()
        except requests.HTTPError as err:
            raise exceptions.PSGConnectionError(reply.content) from err
        too_many_calls = 'Your other API call is still running, please let it finish, wait 10 minutes, or consider installing the PSG Docker version'
        if too_many_calls in reply.text:
            raise exceptions.PSGConnectionError(reply.text)
        parse_exceptions(reply.content)
        if self._type in ['upd', 'set']:
            return PSGResponse.null()
        elif not self.is_single_file:
            return PSGResponse.from_bytes(reply.content)
        elif self._type is None:
            return PSGResponse(rad=PyRad.from_bytes(reply.content))
        else:
            returntype = typedict[self._type.encode(settings.get_setting('encoding'))]
            return PSGResponse(**{self._type:returntype.from_bytes(reply.content)})
