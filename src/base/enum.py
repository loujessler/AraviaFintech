from enum import Enum


class BaseEnum(Enum):
    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(status.name, status.value) for status in cls]
