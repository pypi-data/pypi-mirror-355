"""module description"""

import os
import json
from typing import Optional

from .logger import global_logger

_logger = global_logger


class Params:
    """
    If additional Parameters are needed, add them to the parameters and params_types dictionaries.
    If a parameter is required, add it to the required_params list.
    Also, add them in the constuctor if in the standard module.
    """

    parameters = {
        "results_dir": "",  # str
        "data_h5_file": "",  # str
        "darkframe_dset": "",  # int
        "custom_attributes": {},  # dict
        "nframes_eval": [0, -1, 1],  # list of ints
        "thres_bad_slopes": 3,  # float
        "thres_event_prim": 3,  # float
        "thres_event_sec": 3,  # float
        "ext_offsetmap": "",  # str
        "ext_noisemap": "",  # str
    }

    # types are checked when they are read
    params_types = {
        "results_dir": str,  # str
        "data_h5_file": str,  # str
        "darkframe_dset": str,  # str
        "custom_attributes": dict,  # dict
        "nframes_eval": list,  # list of ints
        "thres_bad_slopes": (int, float),  # float
        "thres_event_prim": (int, float),  # float
        "thres_event_sec": (int, float),  # float
        "ext_offsetmap": str,  # str
        "ext_noisemap": str,  # str
    }

    # required parameters, where there is no default value
    # file cannot be loaded if these are missing
    required_params = ["results_dir", "data_h5_file"]

    def __init__(self, json_path: Optional[str] = None):
        self.default_dict = {**self.parameters}
        self.inp_dict = None
        self.param_dict = None
        if json_path is not None:
            self.update(json_path)
            self.check_types()
        else:
            _logger.error("No parameter file provided.")
            _logger.error("Created default parameter file.")
            self.save_default_file()
            _logger.error("Add all required parameters to default.")
            _logger.error("Add the path to the parameter file as an argument.")
            raise ValueError("No parameter file provided.")

    def update(self, json_path: str) -> None:
        """Function description"""
        try:
            with open(json_path, encoding="utf-8") as f:
                self.inp_dict = json.load(f)
        except Exception as exc:
            _logger.error("Error loading the parameter file.")
            self.save_default_file()
            _logger.error("A default parameter file has been saved to the current directory.")
            self.param_dict = None
            raise ValueError("Error loading the parameter file.") from exc
        self.param_dict = self.default_dict.copy()
        # check consistency of the input dict with the default dict
        for key, value in self.inp_dict.items():
            if key not in self.default_dict:
                self.save_default_file()
                _logger.error("A default parameter file has been saved to the current directory.")
                raise ValueError(f"{key} is not a valid parameter.")
            else:
                self.param_dict[key] = value
        # check for missing parameters, using default if not required
        # if parameter has no default, set param_dict to None
        for key, value in self.param_dict.items():
            if value is None or value == "":
                if key in self.required_params:
                    _logger.error("%s is missing in the file.", key)
                    _logger.error("Please provide a complete parameter file")
                    self.param_dict = None
                    raise ValueError(f"{key} is missing in the file.")

    def check_types(self) -> None:
        """Function description"""
        if self.param_dict is None:
            return None
        for key, value in self.param_dict.items():
            if key not in self.params_types:
                raise TypeError(f"There is no type defined for {key}.")
            else:
                expected_type = self.params_types[key]
                if not isinstance(value, expected_type):
                    raise TypeError(f"Expected {key} to be of type {expected_type}.")

    def get_dict(self) -> dict:
        """Function description"""
        if self.param_dict is None:
            return {}
        return self.param_dict

    def print_contents(self) -> None:
        """Function description"""
        if self.param_dict is None:
            return None
        for key, value in self.param_dict.items():
            _logger.info("%s: %s", key, value)

    def save_default_file(self, path: Optional[str] = None) -> None:
        """Function description"""
        # if no path is provided, save to the current directory
        if path is None:
            path = os.path.join(os.getcwd(), "default_params.json")
        else:
            path = os.path.join(path, "default_params.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.default_dict, f, indent=4)
