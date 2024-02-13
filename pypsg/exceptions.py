"""
PSG Exceptions
"""

class PSGError(Exception):
    """
    The base class for all PSG exceptions.
    """

class GlobESError(PSGError):
    """
    Error in GlobES Application
    """

class PUMASError(PSGError):
    """
    Error in PUMAS Application
    """

class UnknownPSGError(PSGError):
    """
    Unknown PSG Error. If encountered in production submit an issue.
    """

class PSGConnectionError(PSGError):
    """
    PSG Connection Error
    """

class PSGMultiError(PSGError):
    """
    Multiple PSG Errors.
    """

class PSGWarning(UserWarning):
    """
    The base class for all PSG warnings.
    """

class PUMASWarning(PSGWarning):
    """
    Warning in PUMAS Application
    """

class GeneratorWarning(PSGWarning):
    """
    Warning in Generator Application
    """

class UnknownPSGWarning(PSGWarning):
    """
    Unknown PSG Warning. If encountered in production submit an issue.
    """