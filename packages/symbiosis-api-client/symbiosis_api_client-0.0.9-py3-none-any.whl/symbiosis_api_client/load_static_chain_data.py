"""Loads static data from mainnet.json into corresponding models."""

import json
import os

from . import static_models as models_static


def load_static_config(filepath: str | None = None) -> models_static.StaticConfigModel:
    """Load static chains from mainnet.json."""
    # Load the static data from the JSON file
    if filepath is None:
        filepath = os.path.dirname(__file__)
        filepath = os.path.join(filepath, "mainnet.json")

    with open(filepath, "r", encoding="utf-8") as f:
        jsondata = json.load(f)

    data = models_static.StaticConfigModel.model_validate(jsondata)

    return data
