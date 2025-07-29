"""Test the directories module."""
import os
from importlib import resources as impresources

import yaml

import bw2scaffold
from bw2scaffold.directories import create_structure


def check_files_exist(file_dict, parent=""):
    """
    Recursively checks if files exist based on a nested dictionary structure,
    using a parent directory.

    Args:

        file_dict (dict): String values or nested dictionaries as values.
        parent (str): The current directory path to prefix to each key.

    Returns:
        bool: True if all files exist, False otherwise.
    """
    for key, value in file_dict.items():
        # Construct the new path based on the parent and the current key
        current_path = os.path.join(parent, key)

        if isinstance(value, str):
            # Construct the file path based on parent directory and key
            file_path = os.path.join(parent, key)
            if not os.path.isfile(file_path):
                print(f"File does not exist: {file_path}")
                return False
        elif isinstance(value, dict):
            # Recurse deeper into the structure with the updated path
            if not check_files_exist(value, current_path):
                return False
        else:
            # Raise an error for any unexpected value type
            raise ValueError(f"Unexpected value type at key {key}: {type(value)}")

    return True


def test_create_structure(tmp_path):
    """
    Verify that all the required files from the directories.yaml spec are created.

    """
    project_name = "sample project"

    parent = tmp_path / project_name
    create_structure(parent)
    assert parent.exists()

    dirs_file = impresources.files(bw2scaffold) / "templates" / "directories.yaml"
    print(f"test path {tmp_path}")
    print(f"Temp file {dirs_file}")
    with dirs_file.open(mode="r", encoding="utf-8") as f:
        dirs_config = yaml.safe_load(f)

    assert check_files_exist(dirs_config, parent=parent)
