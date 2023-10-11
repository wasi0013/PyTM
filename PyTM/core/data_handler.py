import os
import sys
import json


def init_data(path):
    """
    Creates the data to the given path.
    """
    data = []
    with open(path, "w") as f:
        json.dump(data, f)


def load_data(path):
    """
    Loads the data from the given path.
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_data(path, data):
    """
    Saves the data to the given path.
    """
    if data:
        with open(path, "w") as f:
            json.dump(data, f)


def update(path, func):
    """
    Decorator for updating the data.
    """
    data = load_data(path)
    save_data(path, func(data))
