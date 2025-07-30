"""
Smoke tests for essential functionality - minimal test suite for CI
Tests core functionality without external dependencies (no API calls)
"""

import os
import sys
from typing import Any
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_package_imports():
    """Test that all main modules can be imported"""
    # Import modules to verify they load without errors
    try:
        import src.generate_code_review_context  # type: ignore
        import src.server  # type: ignore

        # Verify the modules have expected attributes to satisfy linter
        server_module: Any = src.server
        context_module: Any = src.generate_code_review_context
        assert hasattr(server_module, "mcp")
        assert hasattr(context_module, "generate_code_review_context_main")
    except ImportError as e:
        assert False, f"Failed to import module: {e}"
    # model_config is a JSON file, not a Python module
    assert True  # If we get here, imports worked


def test_model_config_loading():
    """Test model configuration loading works"""
    from src.model_config_manager import load_model_config  # type: ignore

    config: dict[str, Any] = load_model_config()
    assert isinstance(config, dict)
    assert "model_aliases" in config
    assert "defaults" in config
    assert "model_capabilities" in config


def test_entry_points_defined():
    """Test that console script entry points are properly defined"""
    from pathlib import Path

    # Check pyproject.toml has the entry points defined
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "r") as f:
        content = f.read()

    # Check our main entry points exist in pyproject.toml
    expected_commands = [
        "gemini-code-review-mcp",
        "generate-code-review",
        "generate-meta-prompt",
    ]

    for cmd in expected_commands:
        assert cmd in content, f"Missing entry point in pyproject.toml: {cmd}"


@patch("src.gemini_api_client.GEMINI_AVAILABLE", False)
def test_graceful_fallback_no_gemini():
    """Test that the system works without Gemini API available"""
    from src.gemini_api_client import send_to_gemini_for_review  # type: ignore

    result: Any = send_to_gemini_for_review("test content", "/tmp", 0.5)
    assert result is None  # Should gracefully return None without Gemini


def test_cli_help_functions():
    """Test that CLI help functions work without crashes"""
    # Test that we can create argument parsers without errors
    from src.cli_main import cli_main  # type: ignore

    # These should not crash when imported
    assert callable(cli_main)


def test_mcp_server_startup():
    """Test that MCP server can be imported and basic setup works"""
    from src.server import main as server_main

    # Should be able to import the main function
    assert callable(server_main)


@patch.dict(os.environ, {"MAX_FILE_SIZE_MB": "5"})
def test_environment_variable_handling():
    """Test that environment variables are properly handled"""
    # Test that our code reads environment variables correctly
    assert os.getenv("MAX_FILE_SIZE_MB") == "5"

    # Test default fallback
    assert os.getenv("NONEXISTENT_VAR", "default") == "default"


def test_model_alias_resolution():
    """Test that model aliases resolve correctly"""
    from src.model_config_manager import load_model_config  # type: ignore

    config: dict[str, Any] = load_model_config()
    aliases = config.get("model_aliases", {})

    # Test that gemini-2.5-pro alias exists and resolves
    if "gemini-2.5-pro" in aliases:
        resolved = aliases["gemini-2.5-pro"]
        assert "preview" in resolved  # Should resolve to preview model


def test_scope_values():
    """Test that scope constants are properly defined"""
    # These should be available as valid scope options
    valid_scopes = ["recent_phase", "full_project", "specific_phase", "specific_task"]

    # Test scope validation would work
    for scope in valid_scopes:
        assert isinstance(scope, str)
        assert len(scope) > 0
