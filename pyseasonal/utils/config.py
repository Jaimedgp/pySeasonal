import os

import yaml


def _check_paths_exist(paths_dict: dict):
    """Check if all paths in the dictionary exist"""
    for key, path in paths_dict.items():
        if "filename" in key:
            continue

        if key == "home" and path == "":
            continue

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path for '{key}' does not exist: {key}: '{path}'")

    return True


def load_config(config_path):
    """Load configuration from YAML file"""
    print('The path of the configuration file is '+str(config_path))
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    # Setup paths based on GCM_STORE environment variable
    gcm_store = os.getenv('GCM_STORE', 'lustre')
    if gcm_store in config['paths']:
        paths = config['paths'][gcm_store]
    else:
        raise ValueError('Unknown entry for <gcm_store> !')

    if _check_paths_exist(paths):
        config['paths'] = paths

    return config


if __name__ == '__main__':
    load_config('config/config_for_pred2tercile_operational_medcof_jaimedgp.yaml')
