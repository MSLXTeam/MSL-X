from typing import Union

from .InfoClasses import InfoTypes


class WrongInfoTypeError(Exception):
    def __init__(self, name: str, current_type: Union[InfoTypes, str], correct_type: Union[InfoTypes, str]):
        super().__init__()
        self.name = name
        if isinstance(current_type, InfoTypes):
            self.cutype = current_type.value
        else:
            self.cutype = current_type
        if isinstance(correct_type, InfoTypes):
            self.cotype = correct_type.value
        else:
            self.cotype = correct_type
        self.add_note(f"Type of UniversalInfo {self.name} should be {self.cotype},but it actually {self.cutype}")

    @property
    def __str__(self):
        return f"Type of UniversalInfo {self.name} should be {self.cotype},but it actually {self.cutype}"


class NullEntrypointError(Exception):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    @property
    def __str__(self):
        return f"Object {self.name} doesn't have an available entry point"
