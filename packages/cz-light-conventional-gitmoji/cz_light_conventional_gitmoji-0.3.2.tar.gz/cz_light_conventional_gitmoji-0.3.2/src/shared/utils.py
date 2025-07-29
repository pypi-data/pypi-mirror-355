"""Contains utility functions to work with Gitmoji objects."""

from typing_extensions import LiteralString

from shared.model import Gitmoji
from shared.spec import mojis

# global pattern to validate commit messages
BASE_PATTERN = (
    r"(?s)"
    r"^({type})"
    r"(?:\((\S+)\))?!?: "
    r"{gitmoji_part}"
    r"(?:\r?\n\r?\n(?!\s)(.+)(?<!\s))?$"
)

# Gitmoji required
GITMOJI_REQUIRED = r"(({icon}) (?![\sA-Z])([^\n\r]+)(?<!\s))"

# Gitmoji optional (the whole group is optional, subject still required)
GITMOJI_OPTIONAL = r"((?:{icon} )?(?![\sA-Z])([^\n\r]+)(?<!\s))"

# Usage:
PATTERN_REQUIRED = BASE_PATTERN.replace("{gitmoji_part}", GITMOJI_REQUIRED)
PATTERN_OPTIONAL = BASE_PATTERN.replace("{gitmoji_part}", GITMOJI_OPTIONAL)


def get_gitmojis() -> list[Gitmoji]:
    """Return the list of Gitmoji objects."""
    return [Gitmoji(**moji) for moji in mojis]


def get_type_pattern() -> str:
    """Return the type patterns."""
    return "|".join([moji.type for moji in get_gitmojis()])


def get_icon_pattern() -> str:
    """Return icon patterns."""
    return "|".join([moji.icon for moji in get_gitmojis()])


def _base_get_pattern(pattern: LiteralString) -> str:
    type_pattern = get_type_pattern()
    icon_pattern = get_icon_pattern()

    return pattern.replace("{type}", type_pattern).replace(
        "{icon}", icon_pattern
    )


def get_pattern() -> str:
    """Return the complete validation pattern."""
    return _base_get_pattern(PATTERN_REQUIRED)


def get_pattern_mojify() -> str:
    """Return the complete validation pattern for mojify."""
    return _base_get_pattern(PATTERN_OPTIONAL)
