# tests/unit/scrapers/test_appletv_scraper.py
import typing
import json

import re # Add re import
import pytest
import httpx # Add httpx import
from httpx import Response, HTTPStatusError
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

import datetime as dt # Add datetime import

from isubrip.data_structures import Movie, ScrapedMediaResponse # Add imports
from isubrip.scrapers.appletv_scraper import AppleTVScraper, ScraperError
from isubrip.config import Config
from tests.base import BaseTestWithFs


# Mock data (can be moved to separate files later if needed)
MOCK_CONFIG_DATA_US = {
    "data": {
        "applicationProps": {
            "requiredParamsMap": {
                "Default": {
                    "utscf": "OjAAAAAAAAA~",
                    "caller": "web",
                    "v": "81",
                    "pfm": "web",
                }
            },
            "storefront": {
                "defaultLocale": "en_US",
                "localesSupported": ["en_US", "es_MX", "fr_CA"],
            },
        }
    }
}

MOCK_STOREFRONT_ID_US = "143441"

MOCK_MOVIE_ID = "umc.cmc.mockmovieid123"
MOCK_MOVIE_API_DATA = {
    "data": {
        "id": MOCK_MOVIE_ID,
        "type": "movie",
        "attributes": {"name": "Mock Movie Title"},
        "playables": { # Simplified structure for testing
            "itunes_playable_1": {
                "channelId": "tvs.sbd.9001", # iTunes
                "canonicalId": MOCK_MOVIE_ID,
                "canonicalMetadata": {"movieTitle": "Mock Movie Title", "releaseDate": 1678886400000},
                "itunesMediaApiData": {"id": "123456789", "offers": [{"hlsUrl": "http://mock.itunes.com/playlist.m3u8"}]},
            }
        }
        # ... other fields omitted for brevity
    }
}

MOCK_PLAYABLE_DATA_ITUNES = {
    "channelId": "tvs.sbd.9001", # iTunes
    "canonicalId": MOCK_MOVIE_ID,
    "canonicalMetadata": {
        "movieTitle": "Mock Movie Title",
        "releaseDate": 1678886400000 # Corresponds to 2023-03-15T13:20:00+00:00
    },
    "itunesMediaApiData": {
        "id": "123456789",
        "offers": [
            {"hlsUrl": "http://mock.itunes.com/playlist1.m3u8", "durationInMilliseconds": 7200000}, # 2 hours
            {"hlsUrl": "http://mock.itunes.com/playlist2.m3u8"} # Duplicate URL test? No, different URL
        ],
        "futureRentalAvailabilityDate": "2024-12-31"
    },
}

MOCK_PLAYABLE_DATA_ITUNES_MINIMAL = {
    "channelId": "tvs.sbd.9001", # iTunes
    "canonicalId": "umc.cmc.minimalmovie",
    "canonicalMetadata": {
        "movieTitle": "Minimal Movie",
        "releaseDate": 1640995200000 # 2022-01-01
    },
    "itunesMediaApiData": {
        "id": "987654321",
        # No offers, no duration, no future date
    },
}


class TestAppleTVScraper(BaseTestWithFs):
    """Tests for the AppleTVScraper."""

    @pytest.fixture
    def scraper(self, test_config: Config) -> AppleTVScraper:
        """Fixture to create an AppleTVScraper instance."""
        # The test_config fixture should patch the class variable.
        # The scraper instance reads config from the class variable on init.
        # Explicitly cast to satisfy Pylance due to potential metaclass confusion.
        return typing.cast(AppleTVScraper, AppleTVScraper())

    # === Test Helper Methods ===

    @pytest.mark.parametrize(
        "preferred_locales, default_locale, available_locales, expected_locale",
        [
            # Direct match
            ("fr_FR", "en_US", ["en_US", "fr_FR", "es_ES"], "fr-FR"),
            (["es_ES", "fr_FR"], "en_US", ["en_US", "fr_FR", "es_ES"], "es-ES"),
            # No direct match, fallback to en_*
            ("de_DE", "it_IT", ["en_US", "en_GB", "it_IT"], "en-US"), # Prefers en_US if multiple en_* exist
            ("de_DE", "it_IT", ["en_GB", "it_IT"], "en-GB"),
            # No direct match, no en_*, fallback to default
            ("de_DE", "it_IT", ["fr_FR", "es_ES", "it_IT"], "it_IT"),
            # Preferred is already correct format
            ("fr-FR", "en-US", ["en-US", "fr-FR", "es-ES"], "fr-FR"),
            # Empty preferred, fallback to en_*
            ([], "it_IT", ["en_US", "fr_FR"], "en-US"),
            # Empty preferred, fallback to default
            ([], "it_IT", ["fr_FR", "es_ES"], "it_IT"),
        ],
    )
    def test_decide_locale(
        self,
        scraper: AppleTVScraper,
        preferred_locales: str | list[str],
        default_locale: str,
        available_locales: list[str],
        expected_locale: str,
    ):
        """Test the _decide_locale helper method."""
        result = scraper._decide_locale(preferred_locales, default_locale, available_locales)
        assert result == expected_locale

    # === Test API Interaction Methods ===

    def test_get_configuration_data_success(self, scraper: AppleTVScraper, httpx_mock: HTTPXMock):
        """Test _get_configuration_data successfully fetches and returns data."""
        expected_url = f"{scraper._api_base_url}/configurations?utscf=OjAAAAAAAAA~&caller=web&v=81&pfm=web&sf={MOCK_STOREFRONT_ID_US}"
        httpx_mock.add_response(
            url=expected_url,
            method="GET",
            json=MOCK_CONFIG_DATA_US,
        )

        result = scraper._get_configuration_data(storefront_id=MOCK_STOREFRONT_ID_US)

        assert result == MOCK_CONFIG_DATA_US["data"]
        request = httpx_mock.get_request()
        assert request is not None
        assert str(request.url) == expected_url

    def test_get_configuration_data_http_error(self, scraper: AppleTVScraper, httpx_mock: HTTPXMock):
        """Test _get_configuration_data raises HTTPError on non-200 status."""
        expected_url = f"{scraper._api_base_url}/configurations?utscf=OjAAAAAAAAA~&caller=web&v=81&pfm=web&sf={MOCK_STOREFRONT_ID_US}"
        httpx_mock.add_response(
            url=expected_url,
            method="GET",
            status_code=500,
        )

        with pytest.raises(HTTPStatusError):
            scraper._get_configuration_data(storefront_id=MOCK_STOREFRONT_ID_US)

    @pytest.mark.asyncio
    async def test_fetch_request_params_cache_miss(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test _fetch_request_params when data is not cached."""
        mock_config_data = MOCK_CONFIG_DATA_US["data"]
        mocker.patch.object(
            scraper,
            "_get_configuration_data",
            return_value=mock_config_data,
            autospec=True,
        )
        mocker.patch.object(
            scraper,
            "_decide_locale",
            return_value="en-US", # Mock the locale decision
            autospec=True,
        )

        expected_params = {
            **mock_config_data["applicationProps"]["requiredParamsMap"]["Default"],
            "sf": MOCK_STOREFRONT_ID_US,
            "locale": "en-US",
        }

        # First call - should fetch and cache
        params1 = await scraper._fetch_request_params(storefront_id=MOCK_STOREFRONT_ID_US)
        assert params1 == expected_params
        assert scraper._storefronts_request_params_cache[MOCK_STOREFRONT_ID_US] == expected_params
        scraper._get_configuration_data.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US)
        scraper._decide_locale.assert_called_once_with(
            preferred_locales=["en_US", "en_GB"],
            default_locale=mock_config_data["applicationProps"]["storefront"]["defaultLocale"],
            locales=mock_config_data["applicationProps"]["storefront"]["localesSupported"],
        )

    @pytest.mark.asyncio
    async def test_fetch_request_params_cache_hit(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test _fetch_request_params when data is already cached."""
        mock_get_config = mocker.patch.object(
            scraper,
            "_get_configuration_data",
            autospec=True,
        )
        mock_decide_locale = mocker.patch.object(
            scraper,
            "_decide_locale",
            autospec=True,
        )

        cached_params = {"param1": "value1", "sf": MOCK_STOREFRONT_ID_US, "locale": "en-US"}
        scraper._storefronts_request_params_cache[MOCK_STOREFRONT_ID_US] = cached_params.copy()

        # Second call - should use cache
        params2 = await scraper._fetch_request_params(storefront_id=MOCK_STOREFRONT_ID_US)
        assert params2 == cached_params
        assert params2 is not cached_params # Ensure it's a copy
        mock_get_config.assert_not_called()
        mock_decide_locale.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_api_data_success(self, scraper: AppleTVScraper, httpx_mock: HTTPXMock, mocker: MockerFixture):
        """Test _fetch_api_data successfully fetches and returns data."""
        mock_params = {"param1": "val1", "sf": MOCK_STOREFRONT_ID_US, "locale": "en-US"}
        mocker.patch.object(
            scraper,
            "_fetch_request_params",
            return_value=mock_params.copy(), # Return a copy
            autospec=True,
        )
        endpoint = f"/movies/{MOCK_MOVIE_ID}"
        # Construct URL with parameters
        url_with_params = httpx.URL(f"{scraper._api_base_url}{endpoint}", params=mock_params)

        httpx_mock.add_response(
            url=str(url_with_params), # Pass URL string with params
            method="GET",
            # params=mock_params, # Removed - Params included in URL
            json=MOCK_MOVIE_API_DATA,
        )

        result = await scraper._fetch_api_data(storefront_id=MOCK_STOREFRONT_ID_US, endpoint=endpoint)

        assert result == MOCK_MOVIE_API_DATA["data"]
        scraper._fetch_request_params.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US)
        request = httpx_mock.get_request()
        assert request is not None
        # Check the actual request URL matches the one we mocked
        assert str(request.url) == str(url_with_params)

    @pytest.mark.asyncio
    async def test_fetch_api_data_404_error(self, scraper: AppleTVScraper, httpx_mock: HTTPXMock, mocker: MockerFixture):
        """Test _fetch_api_data raises ScraperError on 404 status."""
        mock_params = {"param1": "val1", "sf": MOCK_STOREFRONT_ID_US, "locale": "en-US"}
        mocker.patch.object(
            scraper,
            "_fetch_request_params",
            return_value=mock_params.copy(),
            autospec=True,
        )
        endpoint = f"/movies/{MOCK_MOVIE_ID}"
        # Construct URL with parameters
        url_with_params = httpx.URL(f"{scraper._api_base_url}{endpoint}", params=mock_params)

        httpx_mock.add_response(
            url=str(url_with_params), # Pass URL string with params
            method="GET",
            # params=mock_params, # Removed
            status_code=404,
        )

        with pytest.raises(ScraperError, match="Media not found"):
            await scraper._fetch_api_data(storefront_id=MOCK_STOREFRONT_ID_US, endpoint=endpoint)

        scraper._fetch_request_params.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US)

    @pytest.mark.asyncio
    async def test_fetch_api_data_other_http_error(self, scraper: AppleTVScraper, httpx_mock: HTTPXMock, mocker: MockerFixture):
        """Test _fetch_api_data raises HTTPStatusError on other non-200 statuses."""
        mock_params = {"param1": "val1", "sf": MOCK_STOREFRONT_ID_US, "locale": "en-US"}
        mocker.patch.object(
            scraper,
            "_fetch_request_params",
            return_value=mock_params.copy(),
            autospec=True,
        )
        endpoint = f"/movies/{MOCK_MOVIE_ID}"
        # Construct URL with parameters
        url_with_params = httpx.URL(f"{scraper._api_base_url}{endpoint}", params=mock_params)

        httpx_mock.add_response(
            url=str(url_with_params), # Pass URL string with params
            method="GET",
            # params=mock_params, # Removed
            status_code=500,
        )

        with pytest.raises(HTTPStatusError):
            await scraper._fetch_api_data(storefront_id=MOCK_STOREFRONT_ID_US, endpoint=endpoint)

        scraper._fetch_request_params.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US)


    # === Test Data Extraction Methods ===

    def test_extract_itunes_movie_data_full(self, scraper: AppleTVScraper):
        """Test _extract_itunes_movie_data with full data."""
        import datetime as dt # Local import for clarity

        movie = scraper._extract_itunes_movie_data(MOCK_PLAYABLE_DATA_ITUNES)

        assert movie.id == "123456789"
        assert movie.referrer_id == MOCK_MOVIE_ID
        assert movie.name == "Mock Movie Title"
        assert movie.release_date == dt.datetime(2023, 3, 15, 13, 20, 0, tzinfo=dt.timezone.utc)
        assert movie.duration == dt.timedelta(milliseconds=7200000)
        assert movie.preorder_availability_date == dt.datetime(2024, 12, 31)
        assert movie.playlist == ["http://mock.itunes.com/playlist1.m3u8", "http://mock.itunes.com/playlist2.m3u8"]

    def test_extract_itunes_movie_data_minimal(self, scraper: AppleTVScraper):
        """Test _extract_itunes_movie_data with minimal data."""
        import datetime as dt # Local import for clarity

        movie = scraper._extract_itunes_movie_data(MOCK_PLAYABLE_DATA_ITUNES_MINIMAL)

        assert movie.id == "987654321"
        assert movie.referrer_id == "umc.cmc.minimalmovie"
        assert movie.name == "Minimal Movie"
        assert movie.release_date == dt.datetime(2022, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
        assert movie.duration is None
        assert movie.preorder_availability_date is None
        assert movie.playlist is None

    # === Test Main Fetching Methods ===

    @pytest.mark.asyncio
    async def test_get_movie_data_success_single_itunes(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_movie_data successfully returns data for a single iTunes playable."""
        mock_api_data = MOCK_MOVIE_API_DATA["data"]
        mock_fetch = mocker.patch.object(
            scraper,
            "_fetch_api_data",
            return_value=mock_api_data,
            autospec=True,
        )
        mock_movie_obj = Movie(id="123456789", name="Mock Movie Title", release_date=dt.datetime.now(dt.timezone.utc))
        mock_extract = mocker.patch.object(
            scraper,
            "_extract_itunes_movie_data",
            return_value=mock_movie_obj,
            autospec=True,
        )

        response = await scraper.get_movie_data(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)

        mock_fetch.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, endpoint=f"/movies/{MOCK_MOVIE_ID}")
        # Expect call with the specific playable data from MOCK_MOVIE_API_DATA
        mock_extract.assert_called_once_with(mock_api_data["playables"]["itunes_playable_1"])
        assert isinstance(response, ScrapedMediaResponse)
        assert response.media_data == [mock_movie_obj]
        assert response.metadata_scraper == scraper.id
        assert response.playlist_scraper == "itunes"
        assert response.original_data == mock_api_data

    @pytest.mark.asyncio
    async def test_get_movie_data_success_multiple_itunes(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_movie_data handles multiple iTunes playables."""
        # Create mock data with two iTunes playables
        mock_api_data_multi = {
            "playables": {
                "itunes1": MOCK_PLAYABLE_DATA_ITUNES.copy(),
                "itunes2": {
                    **MOCK_PLAYABLE_DATA_ITUNES.copy(),
                    "itunesMediaApiData": {
                        "id": "987654321", # Different iTunes ID
                        "offers": [{"hlsUrl": "http://mock.itunes.com/playlist3.m3u8"}]
                    }
                },
                "other_channel": {"channelId": "tvs.sbd.other"}
            }
            # Add other necessary fields if _fetch_api_data mock needs full structure
        }
        mock_fetch = mocker.patch.object(
            scraper, "_fetch_api_data", return_value=mock_api_data_multi, autospec=True
        )

        mock_movie_obj1 = Movie(id="123456789", name="Mock Movie 1", release_date=dt.datetime.now(dt.timezone.utc))
        mock_movie_obj2 = Movie(id="987654321", name="Mock Movie 2", release_date=dt.datetime.now(dt.timezone.utc))
        mock_extract = mocker.patch.object(
            scraper, "_extract_itunes_movie_data", side_effect=[mock_movie_obj1, mock_movie_obj2], autospec=True
        )

        response = await scraper.get_movie_data(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)

        mock_fetch.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, endpoint=f"/movies/{MOCK_MOVIE_ID}")
        assert mock_extract.call_count == 2
        mock_extract.assert_has_calls([ # type: ignore[arg-type]
            mocker.call(mock_api_data_multi["playables"]["itunes1"]),
            mocker.call(mock_api_data_multi["playables"]["itunes2"]),
        ])
        assert response.media_data == [mock_movie_obj1, mock_movie_obj2]
        assert response.playlist_scraper == "itunes"

    @pytest.mark.asyncio
    async def test_get_movie_data_error_no_itunes_only_atvplus(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_movie_data raises error if only AppleTV+ playable exists."""
        mock_api_data_atv = {
            "playables": {
                "atv_plus": {"channelId": scraper.Channel.APPLE_TV_PLUS.value}
            }
        }
        mocker.patch.object(scraper, "_fetch_api_data", return_value=mock_api_data_atv, autospec=True)
        mock_extract = mocker.patch.object(scraper, "_extract_itunes_movie_data", autospec=True)

        expected_error_msg = "Scraping AppleTV+ content is not currently supported."
        with pytest.raises(ScraperError, match=re.escape(expected_error_msg)):
            await scraper.get_movie_data(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_movie_data_error_no_itunes_other_channel(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_movie_data raises error if only non-iTunes/ATV+ playables exist."""
        mock_api_data_other = {
            "playables": {
                "hulu": {"channelId": scraper.Channel.HULU.value},
                "prime": {"channelId": scraper.Channel.PRIME_VIDEO.value},
            }
        }
        mocker.patch.object(scraper, "_fetch_api_data", return_value=mock_api_data_other, autospec=True)
        mock_extract = mocker.patch.object(scraper, "_extract_itunes_movie_data", autospec=True)

        with pytest.raises(ScraperError, match="No iTunes playables could be found."):
            await scraper.get_movie_data(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_movie_data_error_no_playables(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_movie_data raises error if no playables exist at all."""
        mock_api_data_empty = {"playables": {}}
        mocker.patch.object(scraper, "_fetch_api_data", return_value=mock_api_data_empty, autospec=True)
        mock_extract = mocker.patch.object(scraper, "_extract_itunes_movie_data", autospec=True)

        with pytest.raises(ScraperError, match="No iTunes playables could be found."):
            await scraper.get_movie_data(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)
        mock_extract.assert_not_called()


    @pytest.mark.asyncio
    async def test_get_data_movie_url_us_storefront(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data with a movie URL and explicit US storefront."""
        url = f"https://tv.apple.com/us/movie/mock-movie-title/{MOCK_MOVIE_ID}"
        mock_response = ScrapedMediaResponse(media_data=[], metadata_scraper="appletv", playlist_scraper="itunes", original_data={}) # Use empty dict
        mock_get_movie = mocker.patch.object(
            scraper, "get_movie_data", return_value=mock_response, autospec=True
        )

        result = await scraper.get_data(url)

        assert result == mock_response
        mock_get_movie.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)

    @pytest.mark.asyncio
    async def test_get_data_movie_url_no_storefront(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data with a movie URL and no storefront (defaults to US)."""
        url = f"https://tv.apple.com/movie/mock-movie-title/{MOCK_MOVIE_ID}"
        mock_response = ScrapedMediaResponse(media_data=[], metadata_scraper="appletv", playlist_scraper="itunes", original_data={}) # Use empty dict
        mock_get_movie = mocker.patch.object(
            scraper, "get_movie_data", return_value=mock_response, autospec=True
        )

        result = await scraper.get_data(url)

        assert result == mock_response
        # Default storefront is US (143441)
        mock_get_movie.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, movie_id=MOCK_MOVIE_ID)

    @pytest.mark.asyncio
    async def test_get_data_movie_url_other_storefront(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data with a movie URL and a different storefront (GB)."""
        gb_storefront_id = "143444"
        url = f"https://tv.apple.com/gb/movie/another-movie/{MOCK_MOVIE_ID}"
        mock_response = ScrapedMediaResponse(media_data=[], metadata_scraper="appletv", playlist_scraper="itunes", original_data={}) # Use empty dict
        mock_get_movie = mocker.patch.object(
            scraper, "get_movie_data", return_value=mock_response, autospec=True
        )

        result = await scraper.get_data(url)

        assert result == mock_response
        mock_get_movie.assert_called_once_with(storefront_id=gb_storefront_id, movie_id=MOCK_MOVIE_ID)

    @pytest.mark.asyncio
    async def test_get_data_invalid_storefront(self, scraper: AppleTVScraper):
        """Test get_data raises error for an invalid storefront code."""
        url = f"https://tv.apple.com/xx/movie/a-movie/{MOCK_MOVIE_ID}"
        with pytest.raises(ScraperError, match="ID mapping for storefront 'XX' could not be found."):
            await scraper.get_data(url)

    @pytest.mark.asyncio
    async def test_get_data_invalid_url_format(self, scraper: AppleTVScraper):
        """Test get_data raises error for a URL that doesn't match the regex."""
        url = "https://invalid.apple.com/movie/123"
        with pytest.raises(ValueError, match="URL 'https://invalid.apple.com/movie/123' doesn't match"):
            await scraper.get_data(url)

    @pytest.mark.asyncio
    async def test_get_data_episode_url_not_implemented(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data calls get_episode_data (which should raise NotImplementedError)."""
        url = f"https://tv.apple.com/us/episode/ep-title/umc.cmc.episode123"
        mock_get_episode = mocker.patch.object(
            scraper, "get_episode_data", side_effect=NotImplementedError, autospec=True
        )

        with pytest.raises(NotImplementedError):
            await scraper.get_data(url)
        mock_get_episode.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, episode_id="umc.cmc.episode123")

    @pytest.mark.asyncio
    async def test_get_data_season_url_not_implemented(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data calls get_season_data (which should raise NotImplementedError)."""
        url = f"https://tv.apple.com/us/season/season-title/umc.cmc.season456?showId=umc.cmc.show789"
        mock_get_season = mocker.patch.object(
            scraper, "get_season_data", side_effect=NotImplementedError, autospec=True
        )

        with pytest.raises(NotImplementedError):
            await scraper.get_data(url)
        mock_get_season.assert_called_once_with(
            storefront_id=MOCK_STOREFRONT_ID_US, season_id="umc.cmc.season456", show_id="umc.cmc.show789"
        )

    @pytest.mark.asyncio
    async def test_get_data_season_url_missing_showid(self, scraper: AppleTVScraper):
        """Test get_data raises error for season URL missing showId parameter."""
        url = f"https://tv.apple.com/us/season/season-title/umc.cmc.season456"
        with pytest.raises(ScraperError, match="Invalid AppleTV URL: Missing 'showId' parameter."):
            await scraper.get_data(url)

    @pytest.mark.asyncio
    async def test_get_data_show_url_not_implemented(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data calls get_show_data (which should raise NotImplementedError)."""
        url = f"https://tv.apple.com/us/show/show-title/umc.cmc.show789"
        mock_get_show = mocker.patch.object(
            scraper, "get_show_data", side_effect=NotImplementedError, autospec=True
        )

        with pytest.raises(NotImplementedError):
            await scraper.get_data(url)
        mock_get_show.assert_called_once_with(storefront_id=MOCK_STOREFRONT_ID_US, show_id="umc.cmc.show789")

    @pytest.mark.asyncio
    async def test_get_data_invalid_media_type(self, scraper: AppleTVScraper, mocker: MockerFixture):
        """Test get_data raises error for an unknown media type in the URL (if regex allowed it)."""
        # Mock match_url to return a dict with an invalid type
        mock_match_dict = {
            "base_url": "https://tv.apple.com/us/invalidtype/some-name/umc.cmc.123",
            "country_code": "us",
            "media_type": "invalidtype",
            "media_name": "some-name",
            "media_id": "umc.cmc.123",
            "url_params": None,
        }
        mocker.patch.object(scraper, "match_url", return_value=mocker.Mock(groupdict=lambda: mock_match_dict))

        with pytest.raises(ScraperError, match="Invalid media type 'invalidtype'."):
            await scraper.get_data("mock_url") # URL content doesn't matter here as match_url is mocked


    # === Test Error Handling ===
    # TODO: Add tests for error scenarios

    # === Test NotImplemented Methods ===
    # TODO: Add tests for get_episode_data, get_season_data, get_show_data
