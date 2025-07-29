# tests/conftest.py
import pathlib
import sys

import pytest

# Ensure the source directory is in the path for tests to import from isubrip
# Adjust the number of '..' based on the depth of the tests directory
project_root = pathlib.Path(__file__).parent.parent
src_path = project_root / "isubrip"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Import fixtures from modules to make them available globally
# Pytest will automatically discover fixtures in these modules if they are imported here
# or if the modules are specified in pytest's configuration (e.g., pyproject.toml).
# Importing them here makes it explicit.
pytest_plugins = [
    "tests.fixtures.http_mocks",
    "tests.fixtures.fs_mocks",
    "tests.fixtures.async_mocks",
    "tests.fixtures.config_mocks",
]


@pytest.fixture(scope="session")
def mock_data_path() -> pathlib.Path:
    """Fixture to provide the path to the mock data directory."""
    return pathlib.Path(__file__).parent / "mock_data"