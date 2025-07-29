# tests/fixtures/config_mocks.py
import pathlib # Import pathlib
import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

# Corrected imports based on isubrip/config.py
from isubrip.config import (
    Config,
    GeneralCategory,
    DownloadsCategory,
    SubtitlesCategory,
    WebVTTSubcategory,
    DynamicScrapersCategory, # Import the dynamic category
)

# This module provides fixtures for creating Config objects suitable for testing.

@pytest.fixture
def test_config(fs: FakeFilesystem) -> Config:
    """
    Provides a Config object with settings suitable for testing,
    especially using a mocked filesystem.
    """
    # Create a temporary directory within the fake filesystem for output
    mock_output_dir_str = "/mock/test_output"
    mock_output_dir_path = pathlib.Path(mock_output_dir_str) # Convert to Path
    fs.create_dir(mock_output_dir_path) # Use Path object with fs

    # Create a minimal configuration using the correct structure and classes
    config = Config(
        general=GeneralCategory(
            check_for_updates=False, # Disable update checks during tests
            verbose=False,
            log_level="warning", # Keep logs quieter during tests unless needed
            log_rotation_size=1, # Keep log rotation small for tests
        ),
        downloads=DownloadsCategory(
            folder=mock_output_dir_path, # Pass the Path object
            languages=[], # Default to empty, tests can override
            overwrite_existing=False,
            zip=False,
        ),
        subtitles=SubtitlesCategory(
            fix_rtl=False,
            remove_duplicates=True,
            convert_to_srt=False, # Default to WebVTT (or internal format) for tests
            webvtt=WebVTTSubcategory(
                subrip_alignment_conversion=False,
            ),
        ),
        # Use the default factory for the dynamic scrapers category
        # Specific scraper configs can be adjusted in tests if needed
        scrapers=DynamicScrapersCategory(),
    )
    return config

# Add more fixtures for specific config variations if needed
# e.g., a config with convert_to_srt=True, specific languages, etc.