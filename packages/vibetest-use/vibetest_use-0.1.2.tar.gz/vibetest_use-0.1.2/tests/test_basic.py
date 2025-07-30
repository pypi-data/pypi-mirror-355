"""Basic tests for vibetest package."""

import pytest


def test_package_import():
    """Test that the package can be imported."""
    import vibetest
    assert vibetest is not None


def test_mcp_server_import():
    """Test that MCP server module can be imported."""
    try:
        # Set a dummy API key for testing
        import os
        original_key = os.environ.get("GOOGLE_API_KEY")
        os.environ["GOOGLE_API_KEY"] = "test-key-for-import-testing"

        from vibetest.mcp_server import run
        assert callable(run)

        # Restore original key
        if original_key is not None:
            os.environ["GOOGLE_API_KEY"] = original_key
        else:
            del os.environ["GOOGLE_API_KEY"]

    except (ImportError, ValueError) as e:
        # Skip test if dependencies are not installed or other issues
        pytest.skip(f"Skipping MCP server test due to missing dependencies: {e}")


def test_agents_import():
    """Test that agents module can be imported."""
    try:
        # Set a dummy API key for testing
        import os
        original_key = os.environ.get("GOOGLE_API_KEY")
        os.environ["GOOGLE_API_KEY"] = "test-key-for-import-testing"

        import vibetest.agents
        assert vibetest.agents is not None

        # Restore original key
        if original_key is not None:
            os.environ["GOOGLE_API_KEY"] = original_key
        else:
            del os.environ["GOOGLE_API_KEY"]

    except (ImportError, ValueError) as e:
        # Skip test if dependencies are not installed or other issues
        pytest.skip(f"Skipping agents test due to missing dependencies: {e}")


def test_version_exists():
    """Test that version is defined in pyproject.toml."""
    import os
    import sys

    # Try to import tomllib (Python 3.11+) or toml
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            open_mode = "rb"
        else:
            import toml as tomllib
            open_mode = "r"
    except ImportError:
        pytest.skip("Neither tomllib nor toml module available")

    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(__file__))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    with open(pyproject_path, open_mode) as f:
        if sys.version_info >= (3, 11):
            data = tomllib.load(f)
        else:
            data = tomllib.load(f)

    assert "project" in data
    assert "version" in data["project"]
    assert data["project"]["version"] is not None
    assert len(data["project"]["version"]) > 0


def test_package_metadata():
    """Test that package metadata is properly defined."""
    import os
    import sys

    # Try to import tomllib (Python 3.11+) or toml
    try:
        if sys.version_info >= (3, 11):
            import tomllib
            open_mode = "rb"
        else:
            import toml as tomllib
            open_mode = "r"
    except ImportError:
        pytest.skip("Neither tomllib nor toml module available")

    project_root = os.path.dirname(os.path.dirname(__file__))
    pyproject_path = os.path.join(project_root, "pyproject.toml")

    with open(pyproject_path, open_mode) as f:
        if sys.version_info >= (3, 11):
            data = tomllib.load(f)
        else:
            data = tomllib.load(f)

    project = data["project"]

    # Check required fields
    assert project["name"] == "vibetest-use"
    assert "description" in project
    assert "requires-python" in project
    assert "dependencies" in project
    assert isinstance(project["dependencies"], list)
    assert len(project["dependencies"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
