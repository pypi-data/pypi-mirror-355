import logging
from pathlib import Path
from typing import Any, Dict, Union

import yaml


def open_yaml_conf(path: Union[str, Path] = "./image.yml") -> Dict[str, Any]:
    """
    open yaml configuration yaml as a layered dictionary
    """
    logging.info(f"Opening up yaml file {path}")
    with open(path, "r") as f:
        image_conf = yaml.safe_load(f.read())
    return image_conf
