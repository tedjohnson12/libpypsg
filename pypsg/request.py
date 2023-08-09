import requests

from pypsg.cfg.cfg import Config
from pypsg import settings


class apiCall:
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
        cfg: Config,
        output_type: str,
        app: str,
        url: str
    ):
        self.cfg = cfg
        self.type = output_type
        self.app = app
        self.url = url
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
        if not isinstance(self.cfg, Config):
            raise TypeError('apiCall.cfg must be a Config object')
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
        if settings.API_KEY_PATH.exists():
            with open(settings.API_KEY_PATH, encoding='UTF-8') as file:
                data['key'] = file.read()
        reply = requests.post(
            url=self.url,
            data=data,
            timeout=settings.REQUEST_TIMEOUT
        )
        return reply.content
