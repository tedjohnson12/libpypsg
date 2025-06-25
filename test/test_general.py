"""
Some general quality-of-life tests
"""

from pathlib import Path
import pytest

import tomllib
from libpypsg import __version__

import sys

DOCS_SOURCE_PATH = Path(__file__).parent.parent / 'docs' / 'source'
sys.path.append(DOCS_SOURCE_PATH.as_posix())
# pylint: disable-next=import-error
import conf as sphinx_conf

def test_version():
    """
    Check that the version number is the same as in the pyproject.toml
    """
    
    with open(Path(__file__).parent.parent / 'pyproject.toml', 'rb') as f:
        version: str = tomllib.load(f)['project']['version']
    
    assert version == __version__, f'Version in `__init__.py` is {__version__}, but in `pyproject.toml` is {version}'
    
    assert sphinx_conf.release == __version__, f'Version in `pyproject.toml` is {version}, but in `conf.py` is {sphinx_conf.release}'
    
    
if __name__ == '__main__':
    pytest.main(args=[__file__])