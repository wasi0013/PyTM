import json

from PyTM import settings


def init_data(path=settings.data_filepath, data={}):
    """
    Creates the data to the given path.
    """
    with open(path, "w") as f:
        json.dump(data, f)


def load_data(path=settings.data_filepath):
    """
    Loads the data from the given path.
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data, path=settings.data_filepath):
    """
    Saves the data to the given path.
    """
    if data:
        with open(path, "w") as f:
            json.dump(data, f)


def update(func, path=settings.data_filepath):
    """
    Decorator for updating the data.
    """
    data = load_data(path)
    save_data(func(data), path)
