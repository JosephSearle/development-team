"""Integration tests: verify all agent skills directories and SKILL.md files."""

from __future__ import annotations

import importlib.resources
import re
from pathlib import Path

import pytest

_AGENT_SKILLS: list[tuple[str, str]] = [
    ("test_agent", "skills/tdd-test-writing/SKILL.md"),
    ("code_agent", "skills/tdd-implementation/SKILL.md"),
    ("code_review_agent", "skills/code-review/SKILL.md"),
    ("git_agent", "skills/git-conventions/SKILL.md"),
    ("security_agent", "skills/security-scanning/SKILL.md"),
    ("cicd_agent", "skills/cicd-patterns/SKILL.md"),
    ("infrastructure_agent", "skills/k8s-conventions/SKILL.md"),
    ("architecture_agent", "skills/adr-writing/SKILL.md"),
    ("docs_agent", "skills/documentation-standards/SKILL.md"),
    ("dependency_agent", "skills/vulnerability-triage/SKILL.md"),
    ("incident_response_agent", "skills/runbook-writing/SKILL.md"),
]


def _locate_skill(module_name: str, relative_path: str) -> Path:
    pkg = importlib.resources.files(module_name)
    return Path(str(pkg)) / relative_path


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple YAML frontmatter — handles scalar values and inline lists."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        return {}
    result: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


class TestSkillsLoading:
    @pytest.mark.parametrize("module_name,relative_path", _AGENT_SKILLS)
    def test_skill_file_exists_and_is_readable(
        self, module_name: str, relative_path: str
    ) -> None:
        path = _locate_skill(module_name, relative_path)
        assert path.exists(), f"SKILL.md not found at {path}"
        assert path.is_file(), f"SKILL.md path is not a file: {path}"
        text = path.read_text(encoding="utf-8")
        assert len(text) > 0, f"SKILL.md is empty: {path}"

    @pytest.mark.parametrize("module_name,relative_path", _AGENT_SKILLS)
    def test_skill_has_valid_frontmatter(
        self, module_name: str, relative_path: str
    ) -> None:
        path = _locate_skill(module_name, relative_path)
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        assert "name" in fm, f"SKILL.md missing 'name' field: {path}"
        assert len(fm["name"]) > 0, f"SKILL.md 'name' is empty: {path}"

    @pytest.mark.parametrize("module_name,relative_path", _AGENT_SKILLS)
    def test_skill_description_within_1024_chars(
        self, module_name: str, relative_path: str
    ) -> None:
        path = _locate_skill(module_name, relative_path)
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        assert "description" in fm, f"SKILL.md missing 'description' field: {path}"
        desc = fm["description"]
        assert len(desc) <= 1024, (
            f"description is {len(desc)} chars (limit 1024): {path}"
        )

    @pytest.mark.parametrize("module_name,relative_path", _AGENT_SKILLS)
    def test_skill_has_allowed_tools(
        self, module_name: str, relative_path: str
    ) -> None:
        path = _locate_skill(module_name, relative_path)
        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        assert "allowed-tools" in fm, f"SKILL.md missing 'allowed-tools' field: {path}"
        assert re.match(r"^\[.*\]$", fm["allowed-tools"]), (
            f"'allowed-tools' must be an inline list e.g. [tool1, tool2]: {path}"
        )
