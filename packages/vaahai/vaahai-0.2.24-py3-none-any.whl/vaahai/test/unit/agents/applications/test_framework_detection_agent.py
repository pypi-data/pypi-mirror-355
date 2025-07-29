import json
import os
from pathlib import Path

import pytest

from vaahai.agents.applications.framework_detection import FrameworkDetectionAgent


@pytest.fixture
def agent():
    return FrameworkDetectionAgent({"name": "TestFrameworkDetectionAgent"})


def _create_package_json(tmp_path: Path, dependencies: dict):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": dependencies}))


def _create_requirements(tmp_path: Path, packages: list[str]):
    (tmp_path / "requirements.txt").write_text("\n".join(packages))


def test_react_detection(agent, tmp_path):
    _create_package_json(tmp_path, {"react": "^18.2.0"})
    result = agent.run(str(tmp_path))
    assert result["primary_framework"]["name"] == "react"
    assert result["primary_framework"]["confidence"] >= 0.8


def test_django_detection(agent, tmp_path):
    _create_requirements(tmp_path, ["Django==4.2.0"])
    # include manage.py file
    (tmp_path / "manage.py").write_text("import django\n")
    result = agent.run(str(tmp_path))
    assert result["primary_framework"]["name"] == "django"
    assert result["primary_framework"]["confidence"] >= 0.8


def test_wordpress_detection(agent, tmp_path):
    # create WordPress signature file
    (tmp_path / "wp-config.php").write_text("<?php // wp config\n")
    result = agent.run(str(tmp_path))
    assert result["primary_framework"]["name"] == "wordpress"
    assert result["primary_framework"]["confidence"] >= 0.7
    assert result["cms"]["name"] == "wordpress"
