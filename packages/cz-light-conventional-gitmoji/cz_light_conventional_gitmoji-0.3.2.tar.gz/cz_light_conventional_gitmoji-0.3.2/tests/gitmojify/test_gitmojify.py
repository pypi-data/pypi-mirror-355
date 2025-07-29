"""Test the `mojify` module in the `gitmojify` package."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from gitmojify import mojify
from shared.gitmojis import GitMojiConstant as Mojisicon
from shared.spec import mojis

if TYPE_CHECKING:
    from pathlib import Path


def test_grouped_gitmojis() -> None:
    """Verify gitmojis are grouped correctly."""
    grouped_gitmojis = mojify.grouped_gitmojis()
    assert isinstance(grouped_gitmojis, dict)
    assert len(grouped_gitmojis) == len(mojis)


@pytest.mark.parametrize(
    ("message_in", "message_out"),
    [
        (
            "feat: some new feature",
            f"feat: {Mojisicon.GJ_FEAT.value} some new feature",
        ),
        (
            "docs(readme): add a section",
            f"docs(readme): {Mojisicon.GJ_DOCS.value} add a section",
        ),
        (
            "refactor(FooClass)!: rename foo.bar -> foo.baz\n\n"
            "BREAKING CHANGE: this breaks stuff",
            f"refactor(FooClass)!: {Mojisicon.GJ_REFACTOR.value} "
            f"rename foo.bar -> foo.baz\n\nBREAKING CHANGE: this breaks stuff",
        ),
        (
            "test(foo-tests): add some tests for foo\n\n"
            "Add new tests for foo.bar and foo.baz.",
            f"test(foo-tests): {Mojisicon.GJ_TEST.value} "
            f"add some tests for foo\n\n"
            f"Add new tests for foo.bar and foo.baz.",
        ),
    ],
)
def test_gitmojify(message_in: str, message_out: str) -> None:
    """Verify the correct icon is prepended to the message."""
    assert mojify.gitmojify(message_in) == message_out


@pytest.fixture(name="message")
def fixture_message() -> str:
    """Return a commit message."""
    return "feat: some new feature"


@pytest.fixture(name="modified_message")
def fixture_modified_message(message: str) -> str | None:
    """Return the modified commit message or None if not matched."""
    pattern = re.compile(r"([a-zA-Z]+)(\(\S+\))?!?:")
    match = pattern.match(message)
    if match:
        gtype = match.group(1)
        scope = match.group(2) or ""
        return (
            f"{gtype}{scope}: "
            f"{Mojisicon.GJ_FEAT.value}{message[match.end() :]}"
        )
    return None


def test_run_file(
    tmp_path: Path, message: str, modified_message: str | None
) -> None:
    """Verify the commit message is modified."""
    filepath = tmp_path / "commit-msg"
    _ = filepath.write_text(message)
    with mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=mock.MagicMock(
            commit_msg_file=filepath.as_posix(), message=None
        ),
    ):
        mojify.run()

    if modified_message:
        assert filepath.read_text(encoding="utf-8") == modified_message
    else:
        msg = "Message format is invalid"
        raise AssertionError(msg)


def test_run_message(
    message: str,
    modified_message: str | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify the commit message is modified."""
    with mock.patch(
        "argparse.ArgumentParser.parse_args",
        return_value=mock.MagicMock(commit_msg_file=None, message=message),
    ):
        mojify.run()
    captured = capsys.readouterr()
    assert captured.out == modified_message
