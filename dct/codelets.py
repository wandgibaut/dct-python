# ****************************************************************************#
# Copyright (c) 2022  Wandemberg Gibaut                                       #
# All rights reserved. This program and the accompanying materials            #
# are made available under the terms of the MIT License                       #
# which accompanies this distribution, and is available at                    #
# https://opensource.org/licenses/MIT                                         #
#                                                                             #
# Contributors:                                                               #
#      W. Gibaut                                                              #
#                                                                             #
# ****************************************************************************#


from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Union
import json
import time

JsonValue = Union[dict[str, Any], list[Any], str, int, float, bool, None]
JsonObject = dict[str, JsonValue]


class PythonCodelet(ABC):
    """
    Base class for Codelets created in Python
        :param name: name of the codelet
        :param root_codelet_dir: path to the codelet directory
    """

    def __init__(self, name: Optional[str] = None, root_codelet_dir: Optional[Union[str, Path]] = None) -> None:
        if root_codelet_dir is None:
            root_codelet_dir = Path(__file__).resolve().parent
        self.root_codelet_dir = Path(root_codelet_dir)
        self.name = name
        self.fields: JsonObject = self.read_all_field()

    @property
    def fields_path(self) -> Path:
        return self.root_codelet_dir / "fields.json"

    def read_field(self, field: str) -> JsonValue:
        return self.read_all_field()[field]
    
    def read_all_field(self) -> JsonObject:
        with self.fields_path.open(encoding="utf-8") as json_data:
            return json.load(json_data)

    def write_all_field(self) -> None:
        with self.fields_path.open("w", encoding="utf-8") as json_data:
            json.dump(self.fields, json_data)
    
    
    def change_field(self, field: str, value: JsonValue) -> None:
        self.fields[field] = value
        self.write_all_field()

    def add_entry(self, field: str, data: str) -> None:
        with self.fields_path.open("r+", encoding="utf-8") as json_data:
            json_data_contents = json.load(json_data)
            vector = json_data_contents[field]
            vector.append(json.loads(data))
            json_data_contents[field] = vector

            json_data.seek(0)  # rewind
            json.dump(json_data_contents, json_data)
            json_data.truncate()

    def remove_entry(self, field: str, name: str) -> Optional[dict[str, Any]]:
        with self.fields_path.open("r+", encoding="utf-8") as json_data:
            json_data_contents = json.load(json_data)
            vector = json_data_contents[field]

            for i in vector:
                for k, v in i.items():
                    if v == name:
                        vector.remove(i)
                        json_data_contents[field] = vector
                        json_data.seek(0)  # rewind
                        json.dump(json_data_contents, json_data)
                        json_data.truncate()
                        return i

        return None

    def set_field_list(self, field: str, data_list: list[str]) -> None:
        json_list = [json.loads(data_string) for data_string in data_list]

        with self.fields_path.open("r+", encoding="utf-8") as json_data:
            json_data_contents = json.load(json_data)
            json_data_contents[field] = json_list

            json_data.seek(0)  # rewind
            json.dump(json_data_contents, json_data)
            json_data.truncate()

    @staticmethod
    def convert(string: str) -> list[str]:
        return string.split(";")

    def run(self) -> None:
        while bool(self.fields.get("enable")):
            if not bool(self.fields.get("lock")):
                activation = self.calculate_activation()
                self.proc(activation)
            time.sleep(float(self.fields.get("timestep", 0)))
            self.fields = self.read_all_field()

    def calculate_activation(self) -> float:
        """Return the codelet activation used by ``proc``."""
        return 0

    @abstractmethod
    def proc(self, activation: float) -> None:
        """Execute one codelet processing step."""
