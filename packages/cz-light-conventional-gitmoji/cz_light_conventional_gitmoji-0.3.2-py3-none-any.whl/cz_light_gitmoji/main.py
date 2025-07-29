"""
Contains the CommitizenGitmojiCz class.

This is a subclass of BaseCommitizen.
"""

from __future__ import annotations

import re
import textwrap
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import commitizen.defaults
from commitizen import git
from commitizen.cz.base import BaseCommitizen
from commitizen.cz.utils import multiple_line_breaker, required_validator
from commitizen.defaults import MAJOR, MINOR, PATCH
from typing_extensions import override

from shared import utils
from shared.gitmojis import GitMojiConstant as Mojis

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from commitizen.question import CzQuestion

__all__ = ["CommitizenGitmojiCz", "parse_scope", "parse_subject"]


def parse_scope(text: str) -> str:
    """
    Parse the scope of the change.

    :param text: The scope text to parse.
    """
    if not text:
        return ""

    scope = text.strip().split()
    return "-".join(scope)


def parse_subject(text: str | None) -> str:
    """
    Parse the subject of the change.

    :param text: The subject text to parse.
    """
    text = text.strip(".").strip() if text else ""

    return required_validator(text, msg="Subject is required.")


def parse_bordy(text: str) -> str:
    """
    Process the text using multiple_line_breaker and then soft-wrap it.

    :param text: The body text to process.
    """
    processed_text = multiple_line_breaker(text)

    return "\n".join(
        "\n".join(textwrap.wrap(line, width=72))
        for line in processed_text.splitlines()
    )


class CommitizenGitmojiCz(BaseCommitizen):
    """Commitizen adapter for gitmoji style."""

    # pattern to match messages for bumping
    # if none of these matchs, version will not be bumped
    # (unless manually specified)
    bump_pattern = (
        r"^((BREAKING[\-\ ]CHANGE"
        r"|feat"
        r"|fix"
        r"|hotfix"
        r"|refactor"
        r"|perf)"
        r"(\(.+\))?"  # scope
        r"!?):"  # breaking
    )
    # map types to SemVer
    bump_map = OrderedDict(  # noqa: RUF012
        (
            (r"^.+!$", MAJOR),
            (r"^BREAKING[\-\ ]CHANGE", MAJOR),
            (r"^feat", MINOR),
            (r"^fix", PATCH),
            (r"^hotfix", PATCH),
            (r"^refactor", PATCH),
            (r"^perf", PATCH),
        )
    )
    bump_map_major_version_zero = bump_map.copy()

    # parse information for generating the change log
    commit_parser = (
        rf"^(?P<change_type>{utils.get_type_pattern()}|BREAKING CHANGE)"
        rf"(?:\((?P<scope>[^()\r\n]*)\)|\()?(?P<breaking>!)?:\s"
        rf"(?P<emoji>{utils.get_icon_pattern()})?\s?"
        rf"(?P<message>.*)?"
    )
    # exclude from changelog
    changelog_pattern = r"^(?!init)(?!merge)(?!bump).*"
    # map types to changelog sections
    change_type_map = {  # noqa: RUF012
        # features
        "feat": f"{Mojis.GJ_FEAT.value} Features",
        # fixes
        "fix": f"{Mojis.GJ_FIX.value}{Mojis.GJ_HOTFIX.value} Fixes",
        "hotfix": f"{Mojis.GJ_FIX.value}{Mojis.GJ_HOTFIX.value} Fixes",
        # refactorings
        "refactor": f"{Mojis.GJ_REFACTOR.value} Refactorings",
        # style & architecture
        "style": f"{Mojis.GJ_STYLE.value} Style & Architecture",
        # performance
        "perf": f"{Mojis.GJ_PERF.value} Performance",
        # docs
        "docs": f"{Mojis.GJ_DOCS.value} Documentation",
        # tests
        "test": f"{Mojis.GJ_TEST.value} Tests",
        # ci & build
        "build": f"{Mojis.GJ_CI.value}{Mojis.GJ_BUILD.value} CI & Build",
        "ci": f"{Mojis.GJ_CI.value}{Mojis.GJ_BUILD.value} CI & Build",
        # configuration & scripts & packages
        "config": f"{Mojis.GJ_CONFIG.value} Configuration, Scripts, Packages",
        # cleanup
        "dump": f"{Mojis.GJ_DUMP.value} Clean up",
        # dependencies
        "dep-add": (
            f"{Mojis.GJ_DEP_ADD.value}{Mojis.GJ_DEP_RM.value}"
            f"{Mojis.GJ_DEP_BUMP.value}{Mojis.GJ_DEP_DROP.value} Dependencies"
        ),
        "dep-rm": (
            f"{Mojis.GJ_DEP_ADD.value}{Mojis.GJ_DEP_RM.value}"
            f"{Mojis.GJ_DEP_BUMP.value}{Mojis.GJ_DEP_DROP.value} Dependencies"
        ),
        "dep-bump": (
            f"{Mojis.GJ_DEP_ADD.value}{Mojis.GJ_DEP_RM.value}"
            f"{Mojis.GJ_DEP_BUMP.value}{Mojis.GJ_DEP_DROP.value} Dependencies"
        ),
        "dep-drop": (
            f"{Mojis.GJ_DEP_ADD.value}{Mojis.GJ_DEP_RM.value}"
            f"{Mojis.GJ_DEP_BUMP.value}{Mojis.GJ_DEP_DROP.value} Dependencies"
        ),
        # language & accessibility
        "lang": f"{Mojis.GJ_LANG.value} Language & Accessibility",
        # logs
        "logs-add": f"{Mojis.GJ_LOGS_ADD.value}{Mojis.GJ_LOGS_RM.value} Logs",
        "logs-rm": f"{Mojis.GJ_LOGS_ADD.value}{Mojis.GJ_LOGS_RM.value} Logs",
        # ignore
        "ignore": f"{Mojis.GJ_IGNORE.value} Ignore",
        # chore
        "chore": f"{Mojis.GJ_CHORE.value} Chore",
        # None: init, bump, merge
    }
    # Order sections in changelog
    # All other sections are ordered alphabetically
    change_type_order = [  # noqa: RUF012
        f"{Mojis.GJ_FEAT.value} Features",
        f"{Mojis.GJ_FIX.value}{Mojis.GJ_HOTFIX.value} Fixes",
        f"{Mojis.GJ_REFACTOR.value} Refactorings",
        f"{Mojis.GJ_PERF.value} Performance",
    ]
    # message to bump version
    commitizen.defaults.BUMP_MESSAGE = (
        "bump(release): 🔖 $current_version → $new_version"
    )

    @staticmethod
    @override
    def changelog_message_builder_hook(
        message: dict[str, Any], commit: git.GitCommit
    ) -> dict[str, Any] | Iterable[dict[str, Any]] | None:
        """
        Build the changelog message.

        :param message: The parsed commit message
        :param commit: The commit object
        :return: The changelog message.
        """
        if message.get("emoji"):
            message["message"] = (
                message["message"].lstrip(message["emoji"]).lstrip()
            )

        return message

    @override
    def questions(self) -> Iterable[CzQuestion]:
        """Return the questions to ask the user."""
        return [
            {  # pyright: ignore [reportReturnType]
                "type": "list",
                "name": "prefix",
                "message": "Select the type of change you are committing",
                "choices": [
                    {"value": moji.value, "name": moji.name}
                    for moji in utils.get_gitmojis()
                ],
            },
            {
                "type": "input",
                "name": "scope",
                "message": (
                    "What is the scope of this change? (class or file name): "
                    "(press [enter] to skip)\n"
                ),
                "filter": parse_scope,
            },
            {
                "type": "input",
                "name": "subject",
                "message": (
                    "Write a short and imperative summary "
                    "of the code changes: "
                    "(lower case (except for name) and no period)\n"
                ),
                "filter": parse_subject,
            },
            {
                "type": "input",
                "name": "body",
                "message": (
                    "Provide additional contextual information about "
                    "the code changes: (press [enter] to skip)\n"
                ),
                "filter": parse_bordy,
            },
            {
                "type": "confirm",
                "name": "is_breaking_change",
                "message": (
                    "Is this a BREAKING CHANGE? "
                    "Correlates with MAJOR in SemVer"
                ),
                "default": False,
            },
            {
                "type": "input",
                "name": "footer",
                "message": (
                    "Footer. Information about Breaking Changes and reference "
                    "issues that this commit closes: (press [enter] to skip)\n"
                ),
            },
        ]

    @override
    def message(self, answers: Mapping[str, Any]) -> str:
        """Generate a commit message from the answers."""
        prefix: tuple[str, str] = answers["prefix"]
        scope = answers["scope"]
        subject = answers["subject"]
        body = answers["body"]
        footer = answers["footer"]
        is_breaking_change = answers["is_breaking_change"]

        if scope:
            scope = f"({scope})"
        if body:
            body = f"\n\n{body}"
        if (
            is_breaking_change
            and footer
            and not footer.startswith("BREAKING CHANGE")
        ):
            footer = f"BREAKING CHANGE: {footer}"
        if footer:
            footer = f"\n\n{footer}"

        prefix_scope = f"{prefix[0]}{scope}"
        if is_breaking_change:
            prefix_scope = f"{prefix_scope}!"

        return f"{prefix_scope}: {prefix[1]} {subject}{body}{footer}"

    @override
    def example(self) -> str:
        """Return an example commit message."""
        return (
            f"fix: {Mojis.GJ_FIX.value} correct minor typos in code\n"
            "\n"
            "see the issue for details on the typos fixed\n"
            "\n"
            "closes issue #12"
        )

    @override
    def schema(self) -> str:
        """Return the commit message schema."""
        return (
            "<type>(<scope>): <gitmoji> <subject>\n"
            "<BLANK LINE>\n"
            "<body>\n"
            "<BLANK LINE>\n"
            "(BREAKING CHANGE: )<footer>"
        )

    # pattern to validate commits
    @override
    def schema_pattern(self) -> str:
        """Return the schema validation pattern."""
        return utils.get_pattern()

    @override
    def info(self) -> str:
        """Return information about the commit message style."""
        dir_path = Path(__file__).parent
        filepath = dir_path.joinpath("conventional_gitmojis_info.txt")

        return Path(filepath).read_text(encoding="utf-8")

    def process_commit(self, commit: str) -> str:
        """Process a commit."""
        pat = self.schema_pattern()
        m = re.match(pat, commit)
        if m is None:
            return ""
        return m.group(3).strip()
