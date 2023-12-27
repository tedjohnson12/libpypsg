"""
Handling of PSG's Global Emission Spectra (GlobES) application
"""

import numpy as np


class GCM:
    """
    Global Circulation Model (GCM)

    Parameters
    ----------
    header : str
        The header of the GCM. This tells PSG how to interpret the data.
    dat : np.ndarray
        The data of the GCM.
    """
    KEY = 'ATMOSPHERE-GCM-PARAMETERS'
    BIN_KEY = 'BINARY'
    ENCODING = 'UTF-8'

    def __init__(
        self,
        header: str,
        dat: np.ndarray
    ):
        self.header = header
        self.dat = dat

    @classmethod
    def from_cfg(cls, d: dict):
        """
        Read a GCM from a config dict.

        Parameters
        ----------
        d : dict
            A dictionary read from a PSG config file.
        """
        if cls.KEY not in d:
            return None
        if cls.BIN_KEY not in d:
            return None
        header = d[cls.KEY]
        bin_dat: bytes = d[cls.BIN_KEY]
        dat = np.frombuffer(bin_dat, dtype=np.float32)
        return cls(header, dat)

    @property
    def content(self) -> bytes:
        """
        Get the content of the GCM in a format that PSG can read.

        Returns
        -------
        bytes
            The content of the GCM.
        """
        params_line = bytes(f'<{self.KEY}>{self.header}\n', encoding=self.ENCODING)
        start_tag = bytes(f'<{self.BIN_KEY}>', encoding=self.ENCODING)
        end_tag = bytes(f'</{self.BIN_KEY}>', encoding=self.ENCODING)
        dat = self.dat.tobytes(order='C')
        return params_line + b'\n' + start_tag + dat + end_tag
