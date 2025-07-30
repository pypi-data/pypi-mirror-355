import yaml
from aia_utils.toml_utils import get_project_meta
from aia_utils.toml_utils import getVersion, aia_utils_version
__version__ = aia_utils_version()

def generate_manifest(toml_file: str = 'pyproject.toml', custom_properties: dict = {}):
    
    tompl_meta = get_project_meta(toml_file)
    version = tompl_meta['tool']['poetry']['version']
    print(tompl_meta['tool']['poetry']['dependencies'])
    manifest = {
        "version": f"{version}",
        "name": f"{tompl_meta['tool']['poetry']['name']}",
        "description": f"{tompl_meta['tool']['poetry']['description']}",
        "Queue": {
            "version": __version__,
        },
        "dependencies": {
        }
    }
    #print(toml_file["tool"]["poetry"])
    for key, value in tompl_meta['tool']['poetry']['dependencies'].items():
        manifest["dependencies"][key] = value
    manifest.update(custom_properties)
    #manifest = manifest + custom_properties
    with open("target/MANIFEST.MF", "w") as f:
        yaml.dump(manifest, f)
    return manifest