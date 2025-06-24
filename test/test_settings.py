"""
tests for settings
"""

import pytest
from libpypsg import temporary_settings, get_setting

def test_temporary_settings():
    """
    test the temporary settings context
    """
    temp_url = 'http://example.com'
    assert get_setting('url') != temp_url
    with temporary_settings(url=temp_url):
        assert get_setting('url') == temp_url
    assert get_setting('url') != temp_url
    
if __name__ == '__main__':
    pytest.main(args=[__file__])