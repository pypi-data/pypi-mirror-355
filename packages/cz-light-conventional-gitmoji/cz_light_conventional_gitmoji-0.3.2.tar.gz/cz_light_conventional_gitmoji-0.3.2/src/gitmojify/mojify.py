"""Main functionality for the gitmojify pre-commit hook."""

import argparse
import re
import sys
from pathlib import Path

from shared.model import Gitmoji
from shared.utils import get_gitmojis, get_pattern_mojify

UTF8 = "utf-8"


def get_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    _ = group.add_argument("-f", "--commit-msg-file")
    _ = group.add_argument("-m", "--message")
    return parser.parse_args()


def grouped_gitmojis() -> dict[str, Gitmoji]:
    """Return the gitmojis grouped by type."""
    return {moji.type: moji for moji in get_gitmojis()}


def gitmojify(message: str) -> str:
    """
    Gitmojify the commit message.

    If a gitmoji is already present in the message,
    the message is returned as is.
    Otherwise, the gitmoji is looked up by type and prepends
    the message.

    Args:
        message: The complete commit message.

    Returns:
        The gitmojified message.
    """
    pat = re.compile(get_pattern_mojify())
    match = pat.match(message)
    if match is None:
        msg = "invalid commit message"
        raise ValueError(msg)
    gtype = match.group(1)
    if " " in gtype:  # maybe do a better check?
        return message
    icon = grouped_gitmojis()[gtype].icon
    subject_start = match.start(3)
    subject_end = match.end(3)

    return "".join(
        [
            message[:subject_start],
            f"{icon} ",
            message[subject_start:subject_end].lstrip(),
            message[subject_end:],
        ]
    )


def run() -> None:
    """Modify the commit message."""
    args = get_args()
    if args.commit_msg_file:
        filepath = Path(args.commit_msg_file)
        # key 'i18n.commitEncoding' and defaults to UTF-8, get encoding
        # from there.
        msg = filepath.read_text(encoding=UTF8)
        with filepath.open("w", encoding=UTF8) as f:
            _ = f.write(gitmojify(msg))
    else:
        msg = args.message
        _ = sys.stdout.write(gitmojify(msg))
