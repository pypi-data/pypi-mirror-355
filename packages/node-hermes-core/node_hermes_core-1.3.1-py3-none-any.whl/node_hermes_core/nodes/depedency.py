from typing import List

import pydantic_yaml
from node_hermes_core.loader import load_modules
from pydantic import BaseModel, Field
import sys

import json
import subprocess


class HermesDependencies(BaseModel):
    """
    Provides a way to specify dependencies for the configuration file.
    This is a subset of the configuration file that is loaded before the main configuration file.
    """

    modules: List[str] = Field(description="List of modules to import before loading the configuration")
    extra_paths: List[str] = Field(description="List of paths to add to the python path", default_factory=list)
    python_backpack: str | None = Field(description="Path to the python executable to piggyback on", default=None)

    @classmethod
    def from_yaml(cls, file_path: str):
        with open(file_path, "r") as file:
            return pydantic_yaml.parse_yaml_raw_as(cls, file)

    @staticmethod
    def import_from_yaml(file_path: str):
        config = HermesDependencies.from_yaml(file_path)

        # Add the extra paths to the python path
        for path in config.extra_paths:
            sys.path.append(path)

        # Add the piggyback
        # if config.python_backpack:
        #     paths = HermesDependencies.get_sys_path(config.python_backpack)
        #     for path in paths:
        #         sys.path.append(path)

        modules = load_modules(config.modules)
        return modules

    @staticmethod
    def get_sys_path(python_executable):
        """
        Get the sys.path for a given Python executable.

        Parameters:
        python_executable (str): Path to the Python executable (e.g., Python in a virtual environment).

        Returns:
        list: A list of paths that are part of the Python executable's sys.path.
        """
        try:
            # Run the Python command to print sys.path
            result = subprocess.run(
                [python_executable, "-c", "import sys, json; print(json.dumps(sys.path))"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the output as JSON to get the sys.path list
            sys_path = json.loads(result.stdout)

            return sys_path

        except subprocess.CalledProcessError as e:
            print(f"Error executing Python: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding sys.path output: {e}")
            return []
