import os

import yaml


def load_config(config_path):
    """Load configuration from YAML file"""
    print('The path of the configuration file is '+str(config_path))
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    # Setup paths based on GCM_STORE environment variable
    gcm_store = os.getenv('GCM_STORE', 'lustre')
    if gcm_store in config['paths']:
        paths = config['paths'][gcm_store]
        config['paths'] = paths
    else:
        raise ValueError('Unknown entry for <gcm_store> !')

    return config
