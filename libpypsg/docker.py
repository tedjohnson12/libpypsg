"""
Helpers for running psg locally
"""
import json
import subprocess
import platform
import shutil

from . import settings

PSG_LATEST = 'psg:latest'
PSG_CONTAINER_NAME = 'psg'


def _is_docker_installed() -> bool:
    """
    True if docker is installed locally.
    """
    return shutil.which('docker') is not None


def _get_containers_json() -> dict:
    shell = platform.system() == 'Windows'
    raw_output = subprocess.check_output(
        ['docker', 'ps', '-a', '--format', 'json'],
        shell=shell).strip().decode('utf-8')
    ls_output = raw_output.split('\n')
    json_output = '[\n' + ',\n'.join(ls_output) + ']'
    containers_info = json.loads(json_output)
    return containers_info


def is_psg_installed() -> bool:
    """
    Determine if a local version of PSG is installed.

    This function checks all docker containers and compares their
    `RepoTags` attribute to the string `psg:latest`.

    Returns
    -------
    bool
        True if a local version of PSG is installed.

    Notes
    -----
    This function also checks the name of the image. This is important
    because the name is used to start/stop the container. The expected
    name is `psg`.

    Warning
    -------
    Prior to `v0.1.2`, this function would throw an error if the
    docker engine was not installed. Since `v0.1.2`, this function
    returns `False` if the docker engine is not installed.
    """
    if not _is_docker_installed():
        return False
    try:
        containers_info = _get_containers_json()

        for info in containers_info:
            image = info["Image"]
            name = info["Names"]
            if isinstance(name, list):
                named_psg = 'psg' in name
            else:
                named_psg = 'psg' == name
            if image == 'psg' and named_psg:
                return True
        return False
    except json.JSONDecodeError:
        return False


def get_psg_container_info() -> dict:
    """
    Get the psg container.

    Returns
    -------
    dict
        The info for the PSG container.
    """
    try:
        containers_info = _get_containers_json()
        for info in containers_info:
            image = info["Image"]
            name = info["Names"]
            if isinstance(name, list):
                named_psg = 'psg' in name
            else:
                named_psg = 'psg' == name
            if image == 'psg' and named_psg:
                return info
    except json.JSONDecodeError as e:
        raise RuntimeError(
            'Could not parse json output from `docker ps -a --format json`. Is docker installed?') from e


class PSGNotInstalledError(Exception):
    """
    Exception raised when a local version of PSG is not installed.
    """


def is_psg_running() -> bool:
    """
    Determine if a local version of PSG is running.

    Returns
    -------
    bool
        True if a local version of PSG is running.
    """
    container = get_psg_container_info()
    return container['State'] == 'running'


def start_psg(strict=True):
    """
    Start the psg container.

    Parameters
    ----------
    strict : bool, optional
        If True, raise an error if PSG is not installed locally. By default True.
    """
    if not is_psg_installed():
        if strict:
            msg = 'PSG is not installed. '
            url = 'https://psg.gsfc.nasa.gov/helpapi.php#installation'
            msg += f'Visit {url} for installation instructions.'
            raise PSGNotInstalledError(msg)
        else:
            return None
    if not is_psg_running():
        subprocess.call(['docker', 'start', 'psg'])


def stop_psg(strict=True):
    """
    Stop the psg container.

    Parameters
    ----------
    strict : bool, optional
        If True, raise an error if PSG is not installed locally. By default True.
    """
    if not is_psg_installed():
        if strict:
            msg = 'PSG is not installed. '
            url = 'https://psg.gsfc.nasa.gov/helpapi.php#installation'
            msg += f'Visit {url} for installation instructions.'
            raise PSGNotInstalledError(msg)
        else:
            return None
    if is_psg_running():
        subprocess.call(['docker', 'stop', 'psg'])


def set_psg_url(internal=True):
    """
    Set the psg URL. This checks if PSG is installed locally first.

    Parameters
    ----------
    internal : bool, optional
        If True, use the internal psg URL. By default True.
    """
    if internal and is_psg_installed():
        url = settings.INTERNAL_PSG_URL
    else:
        url = settings.PSG_URL
    settings.save_settings(url=url)


def set_url_and_run():
    """
    Set the psg URL and run the container.
    Again, this checks if PSG is installed locally first.

    Parameters
    ----------
    url : str
        The URL to use.
    """
    if is_psg_installed():
        url = settings.INTERNAL_PSG_URL
        start_psg(strict=True)
    else:
        url = settings.PSG_URL
    settings.save_settings(url=url)
