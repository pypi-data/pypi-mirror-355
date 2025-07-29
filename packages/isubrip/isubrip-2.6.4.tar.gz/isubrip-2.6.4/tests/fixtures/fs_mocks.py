# tests/fixtures/fs_mocks.py

# The main `fs` fixture is automatically provided by pyfakefs
# and can be used directly in tests by adding the `fs` argument
# to the test function signature.

# This module can contain helper fixtures that utilize the `fs` fixture
# to set up specific file structures or conditions if needed.

# Example (if needed later):
# import pytest
# from pyfakefs.fake_filesystem import FakeFilesystem
#
# @pytest.fixture
# def setup_mock_output_dir(fs: FakeFilesystem):
#     """Creates a standard mock output directory in the fake filesystem."""
#     mock_output = "/mock/output/dir"
#     fs.create_dir(mock_output)
#     return mock_output