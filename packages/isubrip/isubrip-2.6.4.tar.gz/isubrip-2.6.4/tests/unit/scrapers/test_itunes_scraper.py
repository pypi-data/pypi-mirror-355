# -*- coding: utf-8 -*-
"""Unit tests for the iTunesScraper."""

import typing
import pytest
import httpx
import m3u8
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from isubrip.config import Config
from isubrip.scrapers.itunes_scraper import ItunesScraper, ScraperError
from isubrip.scrapers.appletv_scraper import AppleTVScraper # Needed for mocking
from isubrip.scrapers.scraper import PlaylistLoadError, SubtitlesDownloadError # Import error classes
from isubrip.data_structures import (
    SubtitlesFormat, SubtitlesData, Movie, ScrapedMediaResponse, SubtitlesType, SubtitlesFormatType
)
from tests.base import BaseTestWithFs


class TestItunesScraper(BaseTestWithFs):
    """Unit tests for the ItunesScraper."""

    @pytest.fixture(autouse=True) # Apply patch automatically for tests in this class
    def _patch_scraper_factory(self, mocker: MockerFixture) -> None:
        """Patch ScraperFactory.get_scraper_instance for the duration of the test class."""
        self.mock_appletv_scraper = mocker.MagicMock(spec=AppleTVScraper)
        self.mock_get_scraper_instance = mocker.patch(
            "isubrip.scrapers.itunes_scraper.ScraperFactory.get_scraper_instance",
            return_value=self.mock_appletv_scraper,
            autospec=True,
        )

    @pytest.fixture
    def scraper(self, test_config: Config) -> ItunesScraper:
        """Fixture to create an ItunesScraper instance (uses patched factory)."""
        # Reset the class-level mock before creating a new instance for the test
        self.mock_appletv_scraper.reset_mock()
        # The _patch_scraper_factory fixture ensures get_scraper_instance is mocked
        # before this fixture creates the ItunesScraper instance.
        scraper_instance = ItunesScraper()
        return typing.cast(ItunesScraper, scraper_instance)


    def test_init_calls_scraper_factory(self, scraper: ItunesScraper):
        """Test that __init__ calls ScraperFactory.get_scraper_instance correctly."""
        # The scraper fixture already called __init__ using the patched factory
        self.mock_get_scraper_instance.assert_called_once_with(scraper_id="appletv", raise_error=True)
        assert scraper._appletv_scraper is self.mock_appletv_scraper
    @pytest.mark.asyncio
    async def test_get_data_success(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ):
        """Test get_data successfully finds redirect and calls AppleTVScraper."""
        itunes_url = "https://itunes.apple.com/us/movie/mock-movie/id1234567890"
        redirect_find_url = "https://tv.apple.com/us/movie/id1234567890"
        redirect_target_url = "https://tv.apple.com/us/movie/mock-movie-title/umc.cmc.mockmovieid123"
        mock_appletv_response = ScrapedMediaResponse(
            media_data=[Movie(id="umc.cmc.mockmovieid123", name="Mock Movie Title", release_date=2023)],
            metadata_scraper="appletv",
            playlist_scraper="itunes",
            original_data={"key": "value"},
        )

        # Mock the redirect request
        httpx_mock.add_response(
            url=redirect_find_url,
            method="GET",
            status_code=301,
            headers={"Location": redirect_target_url},
        )

        # Configure the mock AppleTVScraper directly (it's already a mock via the fixture)
        scraper._appletv_scraper.match_url.return_value = True
        scraper._appletv_scraper.get_data.return_value = mock_appletv_response

        result = await scraper.get_data(itunes_url)

        # Assertions
        assert httpx_mock.get_request(url=redirect_find_url) is not None
        # Reset mock before assertion in this specific test
        # self.mock_appletv_scraper.reset_mock() # Resetting in fixture should be enough
        scraper._appletv_scraper.match_url.assert_called_once_with(redirect_target_url)
        scraper._appletv_scraper.get_data.assert_called_once_with(url=redirect_target_url)
        assert result == mock_appletv_response

    @pytest.mark.asyncio
    async def test_get_data_success_double_slash_redirect(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ):
        """Test get_data handles redirect URLs starting with //."""
        self.mock_appletv_scraper.reset_mock() # Reset mock explicitly at the start of the test
        itunes_url = "https://itunes.apple.com/gb/movie/another-movie/id0987654321"
        redirect_find_url = "https://tv.apple.com/gb/movie/id0987654321"
        redirect_target_relative = "//tv.apple.com/gb/movie/another-movie-title/umc.cmc.anotherid"
        redirect_target_absolute = "https://tv.apple.com/gb/movie/another-movie-title/umc.cmc.anotherid"
        mock_appletv_response = ScrapedMediaResponse(
            media_data=[Movie(id="umc.cmc.anotherid", name="Another Movie", release_date=2022)],
            metadata_scraper="appletv",
            playlist_scraper="itunes",
            original_data={},
        )

        httpx_mock.add_response(
            url=redirect_find_url,
            method="GET",
            status_code=301,
            headers={"Location": redirect_target_relative},
        )
        # Configure the mock AppleTVScraper directly
        scraper._appletv_scraper.match_url.return_value = True
        scraper._appletv_scraper.get_data.return_value = mock_appletv_response

        result = await scraper.get_data(itunes_url)

        # Reset mock before assertion in this specific test
        # self.mock_appletv_scraper.reset_mock() # Resetting in fixture should be enough
        scraper._appletv_scraper.match_url.assert_called_once_with(redirect_target_absolute) # Check absolute URL is used
        scraper._appletv_scraper.get_data.assert_called_once_with(url=redirect_target_absolute)
        assert result == mock_appletv_response
    @pytest.mark.asyncio
    async def test_get_data_invalid_url_format(self, scraper: ItunesScraper):
        """Test get_data raises ValueError for a URL that doesn't match the regex."""
        url = "https://invalid.itunes.store/movie/123"
        with pytest.raises(ValueError, match="URL 'https://invalid.itunes.store/movie/123' doesn't match"):
            await scraper.get_data(url)

    @pytest.mark.asyncio
    async def test_get_data_redirect_not_found(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ):
        """Test get_data raises ScraperError if redirect URL is not found (non-301)."""
        itunes_url = "https://itunes.apple.com/us/movie/mock-movie/id1234567890"
        redirect_find_url = "https://tv.apple.com/us/movie/id1234567890"

        # Mock the redirect request to return 404 for all 6 attempts
        for _ in range(6):
            httpx_mock.add_response(
                url=redirect_find_url,
                method="GET",
                status_code=404, # Simulate not found
            )
        # Mock sleep to avoid actual waiting during retries
        mock_sleep = mocker.patch("asyncio.sleep")

        with pytest.raises(ScraperError, match="AppleTV redirect URL not found"):
            await scraper.get_data(itunes_url)

        # Check that retries happened (default 5 retries + initial attempt = 6 calls)
        assert len(httpx_mock.get_requests(url=redirect_find_url)) == 6
        assert mock_sleep.call_count == 5 # Sleep is called between retries

    @pytest.mark.asyncio
    async def test_get_data_redirect_invalid_appletv_url(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ):
        """Test get_data raises ScraperError if redirect URL is not a valid AppleTV URL."""
        self.mock_appletv_scraper.reset_mock() # Reset mock explicitly at the start of the test
        itunes_url = "https://itunes.apple.com/us/movie/mock-movie/id1234567890"
        redirect_find_url = "https://tv.apple.com/us/movie/id1234567890"
        invalid_redirect_target_url = "https://some.other.site/movie"

        httpx_mock.add_response(
            url=redirect_find_url,
            method="GET",
            status_code=301,
            headers={"Location": invalid_redirect_target_url},
        )
        # Configure the mock AppleTVScraper directly
        scraper._appletv_scraper.match_url.return_value = False
        # scraper._appletv_scraper.get_data should not be called

        with pytest.raises(ScraperError, match="Redirect URL is not a valid AppleTV URL."):
            await scraper.get_data(itunes_url)

        # Reset mock before assertion in this specific test
        # self.mock_appletv_scraper.reset_mock() # Resetting in fixture should be enough
        scraper._appletv_scraper.match_url.assert_called_once_with(invalid_redirect_target_url)
        scraper._appletv_scraper.get_data.assert_not_called()


    @pytest.mark.asyncio
    async def test_get_data_appletv_scraper_error(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture,
    ):
        """Test get_data propagates errors from AppleTVScraper.get_data."""
        self.mock_appletv_scraper.reset_mock() # Reset mock explicitly at the start of the test
        itunes_url = "https://itunes.apple.com/us/movie/mock-movie/id1234567890"
        redirect_find_url = "https://tv.apple.com/us/movie/id1234567890"
        redirect_target_url = "https://tv.apple.com/us/movie/mock-movie-title/umc.cmc.mockmovieid123"

        httpx_mock.add_response(
            url=redirect_find_url,
            method="GET",
            status_code=301,
            headers={"Location": redirect_target_url},
        )
        # Configure the mock AppleTVScraper directly
        scraper._appletv_scraper.match_url.return_value = True
        scraper._appletv_scraper.get_data.side_effect = ScraperError("Error from AppleTV")

        with pytest.raises(ScraperError, match="Error from AppleTV"):
            await scraper.get_data(itunes_url)

        # Reset mock before assertion in this specific test
        # self.mock_appletv_scraper.reset_mock() # Resetting in fixture should be enough
        scraper._appletv_scraper.match_url.assert_called_once_with(redirect_target_url)
        scraper._appletv_scraper.get_data.assert_called_once_with(url=redirect_target_url)
# === Test Static Methods ===

    @pytest.mark.parametrize(
        "input_name, expected_output",
        [
            ("English", "English"),
            ("English (forced)", "English"),
            (" Spanish ", "Spanish"), # Test stripping whitespace
            (" French (forced) ", "French"), # Test stripping whitespace with forced
            ("日本語", "日本語"), # Test non-latin characters
            ("日本語 (forced)", "日本語"),
            (None, None), # Test None input
            ("", None), # Test empty string input -> returns None
            (" (forced)", ""), # Test only forced -> returns "" after strip
        ]
    )
    def test_parse_language_name(self, input_name: str | None, expected_output: str | None):
        """Test the static parse_language_name method."""
        # Create a dummy Media object
        mock_media = m3u8.Media(
            uri=None, type=None, group_id=None, language=None, assoc_language=None,
            name=input_name, default=None, autoselect=None, forced=None,
            characteristics=None, subtitles=None, base_uri=None, playlist=None
        )
        assert ItunesScraper.parse_language_name(mock_media) == expected_output
# === Test HLS Methods (Inherited) ===

    @pytest.mark.asyncio
    async def test_load_playlist_success(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
    ):
        """Test load_playlist successfully fetches and parses the main playlist."""
        main_playlist_url = "http://mock.itunes.com/main.m3u8"
        mock_playlist_content = """#EXTM3U
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_ak",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO,LANGUAGE="en",URI="subs/en.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_ak",NAME="Spanish",DEFAULT=NO,AUTOSELECT=YES,FORCED=NO,LANGUAGE="es",URI="subs/es.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_ak",NAME="English (forced)",DEFAULT=NO,AUTOSELECT=NO,FORCED=YES,LANGUAGE="en",URI="subs/en_forced.m3u8"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="video_grp",NAME="Video",DEFAULT=YES,AUTOSELECT=YES,URI="video.m3u8"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1000000,SUBTITLES="subtitles_ak"
video.m3u8
"""
        httpx_mock.add_response(url=main_playlist_url, text=mock_playlist_content)

        playlist = await scraper.load_playlist(main_playlist_url)

        assert isinstance(playlist, m3u8.M3U8)
        assert len(playlist.media) == 4 # 3 subs + 1 video
        # Check if subtitles were identified correctly based on filters
        subtitle_media = [m for m in playlist.media if m.type == "SUBTITLES"]
        assert len(subtitle_media) == 3
        assert httpx_mock.get_request(url=main_playlist_url) is not None

    @pytest.mark.asyncio
    async def test_load_playlist_http_error(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
    ):
        """Test load_playlist raises PlaylistLoadError on fetch failure resulting in empty content."""
        main_playlist_url = "http://mock.itunes.com/main_error.m3u8"
        # Mocking a 404 results in an empty response.text, triggering PlaylistLoadError
        httpx_mock.add_response(url=main_playlist_url, status_code=404, text="")

        with pytest.raises(PlaylistLoadError, match="Received empty response for playlist from server."):
            await scraper.load_playlist(main_playlist_url)

    @pytest.mark.asyncio
    async def test_load_playlist_invalid_content(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mocker: MockerFixture, # Add mocker fixture
    ):
        """Test load_playlist raises ValueError on invalid M3U8 content."""
        main_playlist_url = "http://mock.itunes.com/main_invalid.m3u8"
        # Mock the HTTP response first
        httpx_mock.add_response(url=main_playlist_url, text="doesn't matter")

        # Patch m3u8.loads to raise ValueError, simulating a parsing error
        mock_loads = mocker.patch("m3u8.loads", side_effect=ValueError("Simulated parsing error"))

        # Expect the ValueError raised by the patched m3u8.loads
        with pytest.raises(ValueError, match="Simulated parsing error"):
            await scraper.load_playlist(main_playlist_url)

        # Verify m3u8.loads was called
        mock_loads.assert_called_once()
    @pytest.fixture
    def mock_main_playlist(self) -> m3u8.M3U8:
        """Fixture providing a mock M3U8 playlist object."""
        playlist_content = """#EXTM3U
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_ak",NAME="English",DEFAULT=YES,AUTOSELECT=YES,FORCED=NO,LANGUAGE="en",URI="subs/en.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_vod-ak-amt.tv.apple.com",NAME="Spanish",DEFAULT=NO,AUTOSELECT=YES,FORCED=NO,LANGUAGE="es",URI="subs/es.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subtitles_ak",NAME="English (forced)",DEFAULT=NO,AUTOSELECT=NO,FORCED=YES,LANGUAGE="en",URI="subs/en_forced.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="other_subs",NAME="French",DEFAULT=NO,AUTOSELECT=YES,FORCED=NO,LANGUAGE="fr",URI="subs/fr.m3u8"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio_grp",NAME="English Audio",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="en",URI="audio/en.m3u8"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="video_grp",NAME="Video",DEFAULT=YES,AUTOSELECT=YES,URI="video.m3u8"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1000000,SUBTITLES="subtitles_ak",AUDIO="audio_grp"
video.m3u8
"""
        return m3u8.loads(playlist_content)

    def test_find_matching_media_no_filters(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_media returns all media when no filters are applied (scraper has none by default)."""
        # Note: ItunesScraper itself doesn't define default_playlist_filters, so _playlist_filters is None
        # unless explicitly passed or set via config (which isn't done here).
        # Therefore, find_matching_media without external filters should return all media.
        results = scraper.find_matching_media(mock_main_playlist)
        assert len(results) == len(mock_main_playlist.media)
        assert results == mock_main_playlist.media

    def test_find_matching_media_with_filters(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_media with explicit filters."""
        filters: dict[str, str | list[str]] = {"language": "en", "type": "SUBTITLES"}
        results = scraper.find_matching_media(mock_main_playlist, filters=filters)
        assert len(results) == 2 # English and English (forced)
        assert all(m.language == "en" for m in results)
        assert all(m.type == "SUBTITLES" for m in results)

    def test_find_matching_media_case_insensitive(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_media filters are case-insensitive."""
        filters: dict[str, str | list[str]] = {"language": "EN", "type": "subtitles"} # Uppercase language, lowercase type
        results = scraper.find_matching_media(mock_main_playlist, filters=filters)
        assert len(results) == 2
        assert all(m.language == "en" for m in results)
        assert all(m.type == "SUBTITLES" for m in results)

    def test_find_matching_subtitles_no_language_filter(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_subtitles uses internal filters when no language filter is given."""
        # ItunesScraper._subtitles_filters includes TYPE=SUBTITLES and specific GROUP-IDs
        results = scraper.find_matching_subtitles(mock_main_playlist)
        assert len(results) == 3 # English, Spanish, English (forced) - matching TYPE and GROUP-ID
        assert all(m.type == "SUBTITLES" for m in results)
        assert all(m.group_id in ["subtitles_ak", "subtitles_vod-ak-amt.tv.apple.com"] for m in results)

    def test_find_matching_subtitles_with_language_filter(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_subtitles combines internal filters and language filter."""
        language_filter = ["es", "fr"]
        results = scraper.find_matching_subtitles(mock_main_playlist, language_filter=language_filter)
        # Should find Spanish (matches internal group-id and language)
        # Should NOT find French (doesn't match internal group-id)
        assert len(results) == 1
        assert results[0].language == "es"
        assert results[0].group_id == "subtitles_vod-ak-amt.tv.apple.com"

    def test_find_matching_subtitles_language_filter_no_match(self, scraper: ItunesScraper, mock_main_playlist: m3u8.M3U8):
        """Test find_matching_subtitles returns empty list when language filter doesn't match."""
        language_filter = ["de"] # German - not in playlist
        results = scraper.find_matching_subtitles(mock_main_playlist, language_filter=language_filter)
        assert len(results) == 0
# === Test Helper/Static Methods (Inherited) ===

    @pytest.mark.parametrize(
        "media_attrs, expected_type",
        [
            ({"forced": "YES"}, SubtitlesType.FORCED),
            ({"forced": "NO", "characteristics": "public.accessibility.describes-video"}, SubtitlesType.CC),
            ({"forced": "NO", "characteristics": "public.accessibility.transcribes-spoken-dialog"}, SubtitlesType.CC),
            ({"forced": "NO", "characteristics": None}, None), # Regular
            ({"forced": "NO"}, None), # Regular
            ({}, None), # Regular (missing attributes)
            ({"characteristics": "public.some.other.tag"}, None), # Regular
        ]
    )
    def test_detect_subtitles_type(self, scraper: ItunesScraper, media_attrs: dict, expected_type: SubtitlesType | None):
        """Test detect_subtitles_type correctly identifies forced and CC subs."""
        # Create a dummy Media object with specified attributes
        mock_media = m3u8.Media(
            uri=None, type="SUBTITLES", group_id="subs", language="en", name="Test",
            default=media_attrs.get("default"),
            autoselect=media_attrs.get("autoselect"),
            forced=media_attrs.get("forced"),
            characteristics=media_attrs.get("characteristics"),
            subtitles=None, base_uri=None, playlist=None
        )
        assert scraper.detect_subtitles_type(mock_media) == expected_type

    @pytest.mark.parametrize(
        "media_attrs, expected_desc",
        [
            ({"language": "en", "name": "English", "forced": "NO"}, "English (en)"),
            ({"language": "es", "name": "Spanish (Latin America)", "forced": "NO"}, "Spanish (Latin America) (es)"),
            ({"language": "en", "name": "English (forced)", "forced": "YES"}, "English (en) [Forced]"),
            ({"language": "fr", "name": "French", "forced": "NO", "characteristics": "public.accessibility.describes-video"}, "French (fr) [CC]"),
            ({"language": "de", "name": "German (forced)", "forced": "YES", "characteristics": "public.accessibility.transcribes-spoken-dialog"}, "German (de) [Forced]"), # Forced takes precedence over CC in current implementation
            ({"language": "ja", "name": "日本語", "forced": "NO"}, "日本語 (ja)"),
            # Test case where parse_language_name removes (forced) but detect finds FORCED=YES
            ({"language": "he", "name": "Hebrew (forced)", "forced": "YES"}, "Hebrew (he) [Forced]"),
        ]
    )
    def test_format_subtitles_description(self, scraper: ItunesScraper, media_attrs: dict, expected_desc: str):
        """Test format_subtitles_description produces the correct string."""
        mock_media = m3u8.Media(
            uri=None, type="SUBTITLES", group_id="subs",
            language=media_attrs.get("language"),
            name=media_attrs.get("name"),
            default=media_attrs.get("default"),
            autoselect=media_attrs.get("autoselect"),
            forced=media_attrs.get("forced"),
            characteristics=media_attrs.get("characteristics"),
            subtitles=None, base_uri=None, playlist=None
        )
        # Uses ItunesScraper's parse_language_name implementation
        assert scraper.format_subtitles_description(mock_media) == expected_desc
# === Test Download Methods (Inherited) ===

    @pytest.fixture
    def mock_segment_playlist(self) -> m3u8.M3U8:
        """Fixture for a simple segment playlist."""
        content = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
http://mock.segments.com/segment1.webvtt
#EXTINF:10.0,
http://mock.segments.com/segment2.webvtt
#EXTINF:5.0,
http://mock.segments.com/segment3.webvtt
#EXT-X-ENDLIST
"""
        # Need to set base_uri for absolute_uri to work
        playlist = m3u8.loads(content, uri="http://mock.segments.com/playlist.m3u8")
        return playlist

    @pytest.mark.asyncio
    async def test_download_segments_success(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mock_segment_playlist: m3u8.M3U8,
    ):
        """Test download_segments successfully downloads all segments."""
        mock_content1 = b"WEBVTT - Segment 1"
        mock_content2 = b"WEBVTT - Segment 2"
        mock_content3 = b"WEBVTT - Segment 3"

        httpx_mock.add_response(url="http://mock.segments.com/segment1.webvtt", content=mock_content1)
        httpx_mock.add_response(url="http://mock.segments.com/segment2.webvtt", content=mock_content2)
        httpx_mock.add_response(url="http://mock.segments.com/segment3.webvtt", content=mock_content3)

        results = await scraper.download_segments(mock_segment_playlist)

        assert len(results) == 3
        assert results[0] == mock_content1
        assert results[1] == mock_content2
        assert results[2] == mock_content3
        assert len(httpx_mock.get_requests()) == 3

    @pytest.mark.asyncio
    async def test_download_segments_one_fails(
        self,
        scraper: ItunesScraper,
        httpx_mock: HTTPXMock,
        mock_segment_playlist: m3u8.M3U8,
    ):
        """Test download_segments raises DownloadError if one segment fails."""
        mock_content1 = b"WEBVTT - Segment 1"
        mock_content3 = b"WEBVTT - Segment 3"

        httpx_mock.add_response(url="http://mock.segments.com/segment1.webvtt", content=mock_content1)
        httpx_mock.add_response(url="http://mock.segments.com/segment2.webvtt", status_code=500) # Fail this one
        httpx_mock.add_response(url="http://mock.segments.com/segment3.webvtt", content=mock_content3)

        with pytest.raises(ScraperError, match="One of the subtitles segments failed to download."): # Changed from DownloadError
            await scraper.download_segments(mock_segment_playlist)

    @pytest.mark.asyncio
    async def test_download_subtitles_success_webvtt(
        self,
        scraper: ItunesScraper,
        mocker: MockerFixture,
    ):
        """Test download_subtitles successfully downloads and returns SubtitlesData (WebVTT)."""
        mock_media = m3u8.Media(
            uri="http://mock.playlists.com/sub_playlist.m3u8", type="SUBTITLES", group_id="subs",
            language="en", name="English", forced="NO", default="YES", autoselect="YES",
            base_uri="http://mock.playlists.com/", playlist=None # Ensure base_uri is set
        )
        mock_segment_playlist_obj = mocker.MagicMock(spec=m3u8.M3U8)
        mock_segment_content = [b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nTest line 1",
                                b"00:00:03.000 --> 00:00:04.000\nTest line 2"]
        expected_combined_content = b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nTest line 1\n\n00:00:03.000 --> 00:00:04.000\nTest line 2"

        mock_load = mocker.patch.object(scraper, "load_playlist", return_value=mock_segment_playlist_obj, autospec=True)
        mock_download = mocker.patch.object(scraper, "download_segments", return_value=mock_segment_content, autospec=True)
        mock_parse_lang = mocker.patch.object(scraper, "parse_language_name", return_value="English", autospec=True)
        mock_detect_type = mocker.patch.object(scraper, "detect_subtitles_type", return_value=None, autospec=True)

        result = await scraper.download_subtitles(mock_media, subrip_conversion=False)

        mock_load.assert_called_once_with(url=mock_media.absolute_uri)
        mock_download.assert_called_once_with(playlist=mock_segment_playlist_obj)
        mock_parse_lang.assert_called_once_with(media_data=mock_media)
        mock_detect_type.assert_called_once_with(subtitles_media=mock_media)

        assert isinstance(result, SubtitlesData)
        assert result.language_code == "en"
        assert result.language_name == "English"
        assert result.special_type is None
        assert result.subtitles_format == SubtitlesFormatType.WEBVTT
        assert result.content == expected_combined_content
        assert result.content_encoding == "utf-8" # Default for WebVTT class

    @pytest.mark.asyncio
    async def test_download_subtitles_success_srt(
        self,
        scraper: ItunesScraper,
        mocker: MockerFixture,
    ):
        """Test download_subtitles successfully downloads and returns SubtitlesData (SRT)."""
        mock_media = m3u8.Media(
            uri="http://mock.playlists.com/sub_playlist.m3u8", type="SUBTITLES", group_id="subs",
            language="fr", name="French (forced)", forced="YES", default="NO", autoselect="NO",
            base_uri="http://mock.playlists.com/", playlist=None
        )
        mock_segment_playlist_obj = mocker.MagicMock(spec=m3u8.M3U8)
        mock_segment_content = [b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nBonjour"]
        expected_srt_content = b"1\n00:00:01,000 --> 00:00:02,000\nBonjour" # No trailing newline from pysrt

        mocker.patch.object(scraper, "load_playlist", return_value=mock_segment_playlist_obj, autospec=True)
        mocker.patch.object(scraper, "download_segments", return_value=mock_segment_content, autospec=True)
        # Let parse_language_name run its course
        # Let detect_subtitles_type run its course

        result = await scraper.download_subtitles(mock_media, subrip_conversion=True)

        assert isinstance(result, SubtitlesData)
        assert result.language_code == "fr"
        assert result.language_name == "French" # parse_language_name removes (forced)
        assert result.special_type == SubtitlesType.FORCED # detect_subtitles_type finds forced="YES"
        assert result.subtitles_format == SubtitlesFormatType.SUBRIP
        assert result.content == expected_srt_content
        assert result.content_encoding == "utf-8"

    @pytest.mark.asyncio
    async def test_download_subtitles_load_playlist_fails(
        self,
        scraper: ItunesScraper,
        mocker: MockerFixture,
    ):
        """Test download_subtitles raises SubtitlesDownloadError if load_playlist returns None."""
        mock_media = m3u8.Media(uri="uri", type="SUBTITLES", group_id="g", language="en", name="N", base_uri="base")
        mocker.patch.object(scraper, "load_playlist", return_value=None, autospec=True) # Simulate failure

        with pytest.raises(SubtitlesDownloadError) as exc_info:
            await scraper.download_subtitles(mock_media)

        # Check the original exception wrapped by SubtitlesDownloadError
        assert isinstance(exc_info.value.__cause__, PlaylistLoadError)
        assert "Could not load subtitles M3U8 playlist" in str(exc_info.value.__cause__)
        assert exc_info.value.language_code == "en"

    @pytest.mark.asyncio
    async def test_download_subtitles_download_segments_fails(
        self,
        scraper: ItunesScraper,
        mocker: MockerFixture,
    ):
        """Test download_subtitles raises SubtitlesDownloadError if download_segments fails."""
        mock_media = m3u8.Media(uri="uri", type="SUBTITLES", group_id="g", language="en", name="N", base_uri="base")
        mock_segment_playlist_obj = mocker.MagicMock(spec=m3u8.M3U8)
        mocker.patch.object(scraper, "load_playlist", return_value=mock_segment_playlist_obj, autospec=True)
        mocker.patch.object(scraper, "download_segments", side_effect=ScraperError("Segment DL failed"), autospec=True) # Simulate failure

        with pytest.raises(SubtitlesDownloadError) as exc_info:
            await scraper.download_subtitles(mock_media)

        assert isinstance(exc_info.value.__cause__, ScraperError)
        assert "Segment DL failed" in str(exc_info.value.__cause__)
        assert exc_info.value.language_code == "en"
