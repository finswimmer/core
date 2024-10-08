from __future__ import annotations

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def pyproject_toml(tmp_path: Path) -> Path:
    path = tmp_path / "pyproject.toml"
    with path.open(mode="w", encoding="utf-8"):
        pass
    return path


@pytest.fixture
def build_system_section(pyproject_toml: Path) -> str:
    content = """
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""
    with pyproject_toml.open(mode="a", encoding="utf-8") as f:
        f.write(content)
    return content


@pytest.fixture
def poetry_section(pyproject_toml: Path) -> str:
    content = """
[tool.poetry]
name = "poetry"

[tool.poetry.dependencies]
python = "^3.5"
"""
    with pyproject_toml.open(mode="a", encoding="utf-8") as f:
        f.write(content)
    return content


@pytest.fixture
def project_section(pyproject_toml: Path) -> str:
    content = """
[project]
name = "poetry"
version = "1.0.0"
"""
    with pyproject_toml.open(mode="a", encoding="utf-8") as f:
        f.write(content)
    return content


@pytest.fixture
def project_section_dynamic(pyproject_toml: Path) -> str:
    content = """
[project]
name = "not-poetry"
version = "1.0.0"
dynamic = ["description"]
"""
    with pyproject_toml.open(mode="a", encoding="utf-8") as f:
        f.write(content)
    return content
