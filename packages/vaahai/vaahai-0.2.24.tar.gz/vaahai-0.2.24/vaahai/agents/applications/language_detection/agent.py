"""
Language detection agent implementation.

This module provides a specialized agent that can identify programming languages
from code samples with high accuracy using a combination of pattern matching,
statistical analysis, and LLM-based detection.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from vaahai.agents.base.agent_base import AgentBase
from vaahai.agents.base.agent_registry import AgentRegistry
from vaahai.agents.utils.prompt_manager import PromptManager

# Setup logging
logger = logging.getLogger(__name__)

@AgentRegistry.register("language_detection")
class LanguageDetectionAgent(AgentBase):
    """
    A specialized agent for detecting programming languages from code samples.
    
    This agent uses a combination of pattern-based detection, statistical analysis,
    and LLM-based detection to identify programming languages with high accuracy.
    
    Attributes:
        config (Dict[str, Any]): Configuration dictionary for the agent
        name (str): Name of the agent, defaults to class name if not specified
        prompt_manager (PromptManager): Manager for loading and rendering prompts
        language_patterns (Dict): Dictionary of language patterns and signatures
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Language Detection Agent.
        
        Args:
            config: Configuration dictionary for the agent
        """
        # Call parent's init first to set up self.config
        super().__init__(config)
        
        # Initialize the prompt manager
        self.prompt_manager = PromptManager(agent_type="language_detection", agent_name=self.name)
        
        # Initialize language patterns database
        self.language_patterns = self._initialize_language_patterns()
        
        # Initialize LLM client if available
        self.llm_client = self._initialize_llm_client()
        
        # Cache for previously detected files
        self.detection_cache = {}

    def _initialize_language_patterns(self):
        """
        Initialize language patterns for detection by extension, shebang, and keywords.
        Returns:
            Dict[str, Dict]: Language patterns database
        """
        return {
            "python": {
                "extensions": [".py"],
                "shebang": ["python"],
                "keywords": ["def", "import", "self", "lambda", "yield", "async", "await", "print("],
            },
            "javascript": {
                "extensions": [".js"],
                "shebang": ["node", "js"],
                "keywords": ["function", "const", "let", "var", "=>", "console.log", "export", "import"],
            },
            "typescript": {
                "extensions": [".ts"],
                "keywords": ["interface", "type", ": string", ": number", "export", "import"],
            },
            "java": {
                "extensions": [".java"],
                "keywords": ["public class", "static void main", "import java."],
            },
            "csharp": {
                "extensions": [".cs"],
                "keywords": ["using System", "namespace", "public class", "void Main("],
            },
            "php": {
                "extensions": [".php"],
                "keywords": ["<?php", "echo", "$this->", "function", "public function"],
            },
            "ruby": {
                "extensions": [".rb"],
                "keywords": ["def ", "end", "puts", ":symbol"],
            },
            "go": {
                "extensions": [".go"],
                "keywords": ["package main", "func main()", "import ("],
            },
            "html": {
                "extensions": [".html", ".htm"],
                "keywords": ["<!DOCTYPE html>", "<html>", "<body>", "<head>"],
            },
            "css": {
                "extensions": [".css"],
                "keywords": ["color:", "font-size:", "margin:", "padding:", "background:"],
            },
            "shell": {
                "extensions": [".sh", ".bash"],
                "shebang": ["bash", "sh"],
                "keywords": ["#!/bin/bash", "#!/usr/bin/env bash", "echo ", "$1", "fi", "then", "elif"],
            },
            # Add more languages as needed
        }

    def _initialize_llm_client(self):
        """
        Initialize LLM client for language detection if available.
        
        Returns:
            Optional[Any]: LLM client or None if not available
        """
        # This is a stub for now - in a full implementation, this would
        # initialize a connection to the configured LLM provider
        try:
            # Check if LLM configuration exists
            if "llm" in self.config:
                logger.info("LLM configuration found, but client initialization is not implemented yet")
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
            return None

    def _detect_language_by_extension(self, file_path: str) -> Optional[str]:
        """
        Detect language based on file extension.
        """
        ext = os.path.splitext(file_path)[1].lower()
        for lang, patterns in self.language_patterns.items():
            if "extensions" in patterns and ext in patterns["extensions"]:
                return lang
        return None

    def _detect_language_by_shebang(self, code: str) -> Optional[str]:
        """
        Detect language from shebang line in code.
        """
        lines = code.splitlines()
        if lines and lines[0].startswith("#!"):
            shebang = lines[0][2:]
            for lang, patterns in self.language_patterns.items():
                if "shebang" in patterns:
                    for marker in patterns["shebang"]:
                        if marker in shebang:
                            return lang
        return None

    def _detect_language_by_keywords(self, code: str) -> Optional[Tuple[str, float]]:
        """
        Detect language by keyword frequency in the code sample.
        Returns a tuple of (language, confidence) or None.
        """
        scores = {}
        for lang, patterns in self.language_patterns.items():
            if "keywords" in patterns:
                count = sum(1 for kw in patterns["keywords"] if kw in code)
                if count:
                    scores[lang] = count / len(patterns["keywords"])
        if scores:
            lang = max(scores, key=scores.get)
            return lang, scores[lang]
        return None

    def _detect_language_with_llm(self, code: str) -> Dict[str, Any]:
        """
        Stub for LLM-based detection (to be implemented).
        Returns a dict with language info and confidence.
        """
        # This would use the prompt manager and LLM client in a full implementation
        return {
            "primary_language": {"name": "Unknown", "confidence": 0.0},
            "secondary_languages": [],
            "explanation": "LLM-based detection not yet implemented."
        }

    def run(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the language detection agent on the provided code sample.
        Args:
            code: The code sample as a string
            file_path: Optional file path for extension-based detection
        Returns:
            Dict with detection results
        """
        # 1. Extension-based detection
        ext_lang = self._detect_language_by_extension(file_path) if file_path else None
        # 2. Shebang-based detection
        shebang_lang = self._detect_language_by_shebang(code)
        # 3. Keyword-based detection
        kw_result = self._detect_language_by_keywords(code)

        # Aggregate results
        candidates = []
        if ext_lang:
            candidates.append((ext_lang, 0.7))
        if shebang_lang:
            candidates.append((shebang_lang, 0.8))
        if kw_result:
            candidates.append((kw_result[0], kw_result[1]))

        # Pick the best candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            primary = candidates[0]
            result = {
                "primary_language": {"name": primary[0], "confidence": primary[1]},
                "secondary_languages": [
                    {"name": c[0], "confidence": c[1]} for c in candidates[1:]
                ],
                "explanation": f"Detected by: {'/'.join(set([c[0] for c in candidates]))}"
            }
            return result
        # Fallback to LLM-based detection
        return self._detect_language_with_llm(code)
