"""Contains tests for the cz_light_gitmoji module."""

from __future__ import annotations

from typing import Any

import pytest
from commitizen.cz.exceptions import AnswerRequiredError

from cz_light_gitmoji.main import (
    CommitizenGitmojiCz,
    parse_scope,
    parse_subject,
)
from shared.spec import mojis


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        ("main", "main"),
        ("BaseConfig", "BaseConfig"),
        ("a scope", "a-scope"),
        ("", ""),
    ],
)
def test_parse_scope(scope: str, expected: str) -> None:
    """Verify scope is parsed properly."""
    assert parse_scope(scope) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a subject", "a subject"),
        ("subject", "subject"),
        ("subject ", "subject"),
        ("This is a subject.", "This is a subject"),
    ],
)
def test_parse_subject(text: str, expected: str) -> None:
    """Verify subject is parsed properly."""
    assert parse_subject(text) == expected


@pytest.mark.parametrize("text", ["", None])
def test_missing_subject(text: str | None) -> None:
    """Verify that an empty subject raises an error."""
    with pytest.raises(AnswerRequiredError, match=r"Subject is required."):
        parse_subject(text)  # type: ignore[arg-type]


def test_questions(cz_gitmoji: CommitizenGitmojiCz) -> None:
    """Verify questions are as expected."""
    questions = cz_gitmoji.questions()
    assert isinstance(questions, list)

    list_question = questions[0]
    assert isinstance(list_question, dict)

    choices = list_question.get("choices")
    assert choices is not None
    assert len(choices) == len(mojis)


def test_message(
    cz_gitmoji: CommitizenGitmojiCz, messages: tuple[dict[str, Any], str]
) -> None:
    """Verify the correct commit messages are created from answers."""
    answers, expected = messages
    message = cz_gitmoji.message(answers)
    assert message == expected
