import re

from typing import Union


class FileSize:
    UNITS = ["B", "KB", "MB", "GB"]
    BASE = 10
    UNIT_POWER = 3

    def __init__(self, size: Union[int, str]):
        if isinstance(size, str):
            self.value = self.parse_to_int(size)
        else:
            self.value = size

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"FileSize({self.value})"

    def __value__(self, other) -> int:
        if isinstance(other, FileSize):
            return other.value
        elif isinstance(other, str):
            return self.parse_to_int(other)
        else:
            return int(other)

    def __add__(self, other: Union["FileSize", int, str]):
        return FileSize(self.value + self.__value__(other))

    def humanized(self) -> str:
        return self.humanize(self.value)

    def is_valid(self) -> bool:
        return self.value >= 0

    @classmethod
    def unit_value(cls, unit: str):
        index = cls.UNITS.index(unit)
        return cls.BASE ** (index * cls.UNIT_POWER)

    @classmethod
    def size_pattern(cls):
        num_pattern = r"(?P<value>\d+(\.\d+))"
        tokens = "|".join([tok for tok in cls.UNITS])
        unit = rf"(?P<unit>{tokens})"
        return num_pattern + unit

    @classmethod
    def parse_to_int(cls, size_str: str) -> int:
        if match := re.match(cls.size_pattern(), size_str):
            value = float(match.group("value"))
            unit = match.group("unit")
            return int(value * cls.unit_value(unit))
        return int(size_str)

    @classmethod
    def humanize(cls, size: int):
        unit_factor = cls.BASE**cls.UNIT_POWER
        num = float(size)
        for unit in cls.UNITS[:-1]:
            if abs(num) < unit_factor:
                return f"{num:.1f}{unit}"
            num /= unit_factor
        return f"{num:.1f}{cls.UNITS[-1]}"
