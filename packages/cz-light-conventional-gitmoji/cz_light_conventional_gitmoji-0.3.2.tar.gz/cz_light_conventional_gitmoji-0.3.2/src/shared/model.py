"""Contains the Gitmoji class."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Gitmoji:
    """Class that represents a gitmoji."""

    type: str
    icon: str
    code: str
    desc: str

    @property
    def value(self) -> tuple[str, str]:
        """The value property."""
        return self.type, self.icon

    @property
    def name(self) -> str:
        """The name property."""
        return f"{self.icon} {self.type}: {self.desc}"
