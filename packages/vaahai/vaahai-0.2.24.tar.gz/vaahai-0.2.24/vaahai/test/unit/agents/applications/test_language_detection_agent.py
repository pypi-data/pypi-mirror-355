import pytest
from vaahai.agents.applications.language_detection.agent import LanguageDetectionAgent

@pytest.fixture
def agent():
    config = {"name": "TestLanguageDetectionAgent"}
    return LanguageDetectionAgent(config)

def test_extension_detection(agent):
    py_code = "def foo():\n    pass"
    result = agent.run(py_code, file_path="example.py")
    assert result["primary_language"]["name"] == "python"
    assert result["primary_language"]["confidence"] >= 0.7

def test_shebang_detection(agent):
    bash_code = "#!/bin/bash\necho Hello"
    result = agent.run(bash_code, file_path="script.txt")
    assert result["primary_language"]["name"] == "shell"
    assert result["primary_language"]["confidence"] >= 0.8

def test_keyword_detection(agent):
    js_code = "function foo() {\n  console.log('hi');\n}"
    result = agent.run(js_code, file_path="foo.unknown")
    assert result["primary_language"]["name"] == "javascript"
    assert result["primary_language"]["confidence"] > 0.0

def test_aggregate_detection_priority(agent):
    code = "#!/usr/bin/env python3\ndef foo():\n    pass"
    result = agent.run(code, file_path="foo.py")
    # Shebang should take priority over extension if confidence is higher
    assert result["primary_language"]["name"] in ("python", "shell")
    assert result["primary_language"]["confidence"] >= 0.7

def test_llm_fallback(agent):
    unknown_code = "ThisIsNotARealLanguage"
    result = agent.run(unknown_code, file_path="foo.unknown")
    assert result["primary_language"]["name"] == "Unknown"
    assert result["primary_language"]["confidence"] == 0.0
    assert "LLM-based detection not yet implemented" in result["explanation"]
