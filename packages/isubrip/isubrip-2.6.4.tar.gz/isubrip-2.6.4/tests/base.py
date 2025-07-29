# tests/base.py
import pytest

# This module can contain base classes for tests to inherit from,
# providing common setup or utilities.

@pytest.mark.usefixtures("fs")
class BaseTestWithFs:
    """
    Base class for tests that require a mocked filesystem.

    Inheriting from this class automatically applies the `fs` fixture
    provided by pyfakefs, so tests don't need to explicitly request it
    in their signature or use the marker themselves.
    """
    # You can add common helper methods or setup related to the filesystem here
    # if needed in the future.
    pass

# Add other base classes as needed (e.g., for tests requiring specific mocks).