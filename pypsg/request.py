
from typing import Union
import requests

from pypsg.cfg import PyConfig, BinaryConfig
from pypsg import settings


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
        cfg: Union[BinaryConfig, PyConfig],
        output_type:str = None,
        app: str = None,
        url: str = None
    ):
        self.cfg = cfg
        self.type = output_type
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
        if not isinstance(self.cfg, (PyConfig, BinaryConfig)):
            raise TypeError('apiCall.cfg must be a PyConfig or BinaryConfig object')
        if not (isinstance(self.type, str) or self.type is None):
            raise TypeError('apiCall.type must be a string or None')
        if not (isinstance(self.app, str) or self.app is None):
            raise TypeError('apiCall.app must be a string or None')
        if not isinstance(self.url, str):
            raise TypeError('apiCall.url must be a string')

    def __call__(self) -> bytes:
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
        reply = requests.post(
            url=self.url,
            data=data,
            timeout=settings.REQUEST_TIMEOUT
        )
        return reply.content
