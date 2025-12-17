import os

import yaml


def _check_paths_exist(paths_dict: dict) -> bool:
    """Check if all paths in the dictionary exist"""
    for key, path in paths_dict.items():
        if "filename" in key:
            continue

        if key == "home" and path == "":
            continue

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path for '{key}' does not exist: {key}: '{path}'")

    return True


def load_config(config_path) -> dict:
    """Load configuration from YAML file"""
    print("The path of the configuration file is " + str(config_path))
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    if _check_paths_exist(config["paths"]):
        return config

    return {}


if __name__ == "__main__":
    load_config("config/config_for_pred2tercile_operational_medcof_jaimedgp.yaml")
