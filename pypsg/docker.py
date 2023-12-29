"""
Helpers for running psg locally
"""
import docker

from . import settings

PSG_LATEST = 'psg:latest'
PSG_CONTAINER_NAME = 'psg'

def is_psg_installed()->bool:
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
    try:
        installed_containers = docker.from_env().containers.list(all=True)
        for container in installed_containers:
            image = container.image
            if PSG_LATEST in image.attrs['RepoTags']:
                if container.name == PSG_CONTAINER_NAME:
                    return True
        return False
    except docker.errors.DockerException:
        return False

def get_psg_container()->docker.models.containers.Container:
    """
    Get the psg container.
    
    Returns
    -------
    docker.models.containers.Container
        The psg container.
    """
    return docker.from_env().containers.get(PSG_CONTAINER_NAME)

class PSGNotInstalledError(Exception):
    """
    Exception raised when a local version of PSG is not installed.
    """

def is_psg_running()->bool:
    """
    Determine if a local version of PSG is running.
    
    Returns
    -------
    bool
        True if a local version of PSG is running.
    """
    try:
        container = get_psg_container()
    except docker.errors.NotFound as e:
        msg = 'PSG is not installed. '
        url = 'https://psg.gsfc.nasa.gov/helpapi.php#installation'
        msg += f'Visit {url} for installation instructions.'
        raise PSGNotInstalledError(msg) from e
    return container.status == 'running'

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
        get_psg_container().start()

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
        get_psg_container().stop()

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
