from __future__ import annotations

from pathlib import Path

import pytest

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.vcs_dependency import VCSDependency
from poetry.core.pyproject.exceptions import PyProjectError
from poetry.core.pyproject.toml import PyProjectTOML
from poetry.core.utils._compat import tomllib


def test_pyproject_toml_simple(
    pyproject_toml: Path, build_system_section: str, poetry_section: str
) -> None:
    with pyproject_toml.open("rb") as f:
        data = tomllib.load(f)
    assert PyProjectTOML(pyproject_toml).data == data


def test_pyproject_toml_no_poetry_config(pyproject_toml: Path) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert not pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_no_poetry_config_but_project_section(
    pyproject_toml: Path, project_section: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_no_poetry_config_but_project_section_but_dynamic(
    pyproject_toml: Path, project_section_dynamic: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)

    assert not pyproject.is_poetry_project()

    with pytest.raises(PyProjectError) as excval:
        _ = pyproject.poetry_config

    assert f"[tool.poetry] section not found in {pyproject_toml.as_posix()}" in str(
        excval.value
    )


def test_pyproject_toml_poetry_config(
    pyproject_toml: Path, poetry_section: str
) -> None:
    pyproject = PyProjectTOML(pyproject_toml)
    with pyproject_toml.open("rb") as f:
        doc = tomllib.load(f)
    config = doc["tool"]["poetry"]

    assert pyproject.is_poetry_project()
    assert pyproject.poetry_config == config


def test_pyproject_toml_no_build_system_defaults() -> None:
    pyproject_toml = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_with_build_system_requires"
        / "pyproject.toml"
    )

    build_system = PyProjectTOML(pyproject_toml).build_system
    assert build_system.requires == ["poetry-core", "Cython~=0.29.6"]

    assert len(build_system.dependencies) == 2
    assert build_system.dependencies[0].to_pep_508() == "poetry-core"
    assert build_system.dependencies[1].to_pep_508() == "Cython (>=0.29.6,<0.30.0)"


def test_pyproject_toml_build_requires_as_dependencies(pyproject_toml: Path) -> None:
    build_system = PyProjectTOML(pyproject_toml).build_system
    assert build_system.requires == ["setuptools", "wheel"]
    assert build_system.build_backend == "setuptools.build_meta:__legacy__"


def test_pyproject_toml_non_existent(pyproject_toml: Path) -> None:
    pyproject_toml.unlink()
    pyproject = PyProjectTOML(pyproject_toml)
    build_system = pyproject.build_system

    assert pyproject.data == {}
    assert build_system.requires == ["poetry-core"]
    assert build_system.build_backend == "poetry.core.masonry.api"


def test_unparseable_pyproject_toml() -> None:
    pyproject_toml = (
        Path(__file__).parent.parent
        / "fixtures"
        / "project_duplicate_dependency"
        / "pyproject.toml"
    )

    with pytest.raises(PyProjectError) as excval:
        _ = PyProjectTOML(pyproject_toml).build_system

    assert (
        f"{pyproject_toml.as_posix()} is not a valid TOML file.\n"
        "TOMLDecodeError: Cannot overwrite a value (at line 7, column 16)\n"
        "This is often caused by a duplicate entry"
    ) in str(excval.value)


def test_get_dependencies_from_project(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text(
        """\
        [project]
        name="simple"
        version="0.1.0"
        dependencies = [
            "foo",
            "bar>=1.0",
            "Foo_bar"
        ]
        """
    )
    pyproject = PyProjectTOML(pyproject_toml)
    assert pyproject.get_dependencies() == [
        Dependency(name="foo", constraint="*"),
        Dependency(name="bar", constraint=">=1.0"),
        Dependency(name="foo-bar", constraint="*"),
    ]


def test_get_dependencies_from_poetry(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text(
        """\
        [tool.poetry]
        name="simple"
        version="0.1.0"

        [tool.poetry.dependencies]
        foo = "*"
        bar = ">=1.0"
        Foo_bar = { version = "*" }
        """
    )
    pyproject = PyProjectTOML(pyproject_toml)

    assert pyproject.get_dependencies() == [
        Dependency(name="foo", constraint="*"),
        Dependency(name="bar", constraint=">=1.0"),
        Dependency(name="foo-bar", constraint="*"),
    ]


def test_get_dependencies_from_poetry_on_dynamic(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text(
        """\
        [project]
        name="simple"
        version="0.1.0"
        dynamic = ["dependencies"]

        [tool.poetry.dependencies]
        foo = "*"
        bar = ">=1.0"
        Foo_bar = { version = "*" }
        """
    )
    pyproject = PyProjectTOML(pyproject_toml)

    assert pyproject.get_dependencies() == [
        Dependency(name="foo", constraint="*"),
        Dependency(name="bar", constraint=">=1.0"),
        Dependency(name="foo-bar", constraint="*"),
    ]


def test_get_dependencies_from_project_enrich(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text(
        """\
        [project]
        name="simple"
        version="0.1.0"
        dependencies = [
            "foo",
            "poetry @ git+https://github.com/python-poetry/poetry.git"
        ]

        [tool.poetry.dependencies]
        poetry = { develop = true }
        """
    )
    pyproject = PyProjectTOML(pyproject_toml)
    dependencies = pyproject.get_dependencies()
    assert len(dependencies) == 2

    assert isinstance(dependencies[1], VCSDependency)
    assert dependencies[1].name == "poetry"
    assert dependencies[1]._source == "https://github.com/python-poetry/poetry.git"
    assert dependencies[1]._develop is True
