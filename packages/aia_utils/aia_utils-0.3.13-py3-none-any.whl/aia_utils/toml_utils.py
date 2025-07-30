import tomli
from importlib.metadata import version

def get_project_meta(toml_file: str = 'pyproject.toml'):
    with open(toml_file, mode='rb') as pyproject:
        return tomli.load(pyproject)

def _get_project_meta(toml_file: str = 'pyproject.toml'):
    return get_project_meta(toml_file)['tool']['poetry']

def getVersion(toml_file: str = 'pyproject.toml'):
    return _get_project_meta(toml_file)['version']

def aia_utils_version():
    return version('aia-utils')