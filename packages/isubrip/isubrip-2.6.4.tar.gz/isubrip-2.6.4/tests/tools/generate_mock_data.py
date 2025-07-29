# tests/tools/generate_mock_data.py
import argparse
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to sys.path to allow importing isubrip
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from isubrip.config import Config  # Assuming we might need config loading
from isubrip.constants import TEMP_FOLDER_PATH # For potential temp operations
from isubrip.data_structures import PlaylistMediaItem
# from isubrip.logger import setup_loggers # Use basicConfig for this script
from isubrip.scrapers.scraper import Scraper, ScraperFactory, HLSScraper, PlaylistLoadError, DownloadError

# Setup basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("generate_mock_data")


async def fetch_and_save_mock_data(
    scraper_id: str,
    media_url: str, # Full URL for the media item
    output_base_dir: Path,
    languages: list[str] | None = None,
):
    """Fetches playlists and subtitle segments for a given media URL and saves them."""
    # Extract a safe directory name from the URL (e.g., the ID part)
    match = ScraperFactory.get_scraper_instance(scraper_id=scraper_id).match_url(media_url)
    media_dir_name = match.groupdict().get("media_id", Path(media_url).name) if match else Path(media_url).name
    log.info(f"Processing scraper '{scraper_id}' for media URL '{media_url}' (saving to '{media_dir_name}')...")
    output_dir = output_base_dir / scraper_id / media_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)

    scraper = None # Initialize scraper to None for finally block
    try:
        scraper = ScraperFactory.get_scraper_instance(scraper_id=scraper_id, raise_error=True)

        if not isinstance(scraper, HLSScraper):
            log.warning(f"Scraper '{scraper_id}' is not an HLSScraper. Skipping playlist/segment download.")
            return

        # 1. Get Media Data
        log.info(f"Fetching media data for {media_url} using {scraper.name} scraper...")
        scraped_data = await scraper.get_data(url=media_url)

        if not scraped_data or not scraped_data.media_data:
            log.error(f"Could not retrieve media data for {media_url}")
            return

        # Assuming the first item in media_data is the relevant one (e.g., Movie)
        media_item = scraped_data.media_data[0]
        media_title = getattr(media_item, 'name', getattr(media_item, 'series_name', 'Unknown Title')) # Get title attribute
        log.info(f"Successfully retrieved media data. Title: {media_title}")

        # 2. Load Main Playlist from the retrieved media data
        playlist_url_or_urls = getattr(media_item, 'playlist', None)
        if not playlist_url_or_urls:
            log.error(f"No playlist URL found in scraped data for {media_url}")
            return

        # Use the first URL if it's a list
        main_playlist_load_url = playlist_url_or_urls[0] if isinstance(playlist_url_or_urls, list) else playlist_url_or_urls
        log.info(f"Attempting to load main playlist from: {main_playlist_load_url}")
        main_playlist = await scraper.load_playlist(url=main_playlist_load_url)

        if not main_playlist:
            log.error(f"Could not load main playlist for {media_url} from {main_playlist_load_url}")
            return

        # Save Main Playlist
        main_playlist_path = output_dir / "main.m3u8"
        # The base_uri should be set automatically by m3u8.loads when uri is provided.
        # No need to check/set main_playlist.uri here.
        main_playlist_path.write_text(main_playlist.dumps(), encoding="utf-8")
        log.info(f"Saved main playlist to: {main_playlist_path}")

        # 3. Find and Load Subtitle Playlists # Renumbered step
        log.info(f"Searching for subtitle playlists (Languages: {languages or 'all'})...")
        subtitle_media_items = scraper.find_matching_subtitles(main_playlist, language_filter=languages)
        if not subtitle_media_items:
            log.warning(f"No matching subtitles found for languages: {languages or 'all'}")
            return

        log.info(f"Found {len(subtitle_media_items)} matching subtitle playlist(s).")
        for sub_media in subtitle_media_items:
            lang_code = sub_media.language or "unknown"
            sub_type = scraper.detect_subtitles_type(sub_media)
            sub_type_suffix = f".{sub_type.value.lower()}" if sub_type else ""
            playlist_filename = f"subtitles_{lang_code}{sub_type_suffix}.m3u8"
            playlist_path = output_dir / playlist_filename
            log.info(f"Processing subtitle playlist: {sub_media.absolute_uri}")

            try:
                subtitle_playlist = await scraper.load_playlist(url=sub_media.absolute_uri)
                if not subtitle_playlist:
                    log.warning(f"Could not load subtitle playlist: {sub_media.absolute_uri}")
                    continue

                playlist_path.write_text(subtitle_playlist.dumps(), encoding="utf-8")
                log.info(f"Saved subtitle playlist to: {playlist_path}")

                # 3. Download and Save Segments
                segments_dir = output_dir / f"segments_{lang_code}{sub_type_suffix}"
                segments_dir.mkdir(exist_ok=True)
                log.info(f"Downloading segments for {lang_code}{sub_type_suffix}...")

                try:
                    segment_data_list = await scraper.download_segments(subtitle_playlist)
                    log.info(f"Downloaded {len(segment_data_list)} segments.")
                    for i, segment_data in enumerate(segment_data_list):
                        # Use segment URI filename or index, handle None case
                        segment_uri = subtitle_playlist.segments[i].uri
                        if segment_uri:
                            segment_filename = Path(segment_uri).name
                        else:
                            segment_filename = f"segment_{i:03d}.vtt" # Default if URI is None

                        if not segment_filename: # Fallback if name extraction failed (e.g., empty string)
                             segment_filename = f"segment_{i:03d}.vtt" # Adjust extension if needed

                        segment_path = segments_dir / segment_filename
                        segment_path.write_bytes(segment_data)
                    log.info(f"Saved {len(segment_data_list)} segments to: {segments_dir}")

                except DownloadError as e:
                    log.error(f"Failed to download segments for {playlist_path.name}: {e}")
                except Exception as e:
                     log.error(f"Unexpected error downloading segments for {playlist_path.name}: {e}", exc_info=True)


            except PlaylistLoadError as e:
                log.error(f"Failed to load playlist {playlist_path.name}: {e}")
            except Exception as e:
                 log.error(f"Unexpected error processing playlist {playlist_path.name}: {e}", exc_info=True)


    except Exception as e:
        log.error(f"Failed to process {scraper_id} / {media_url}: {e}", exc_info=True) # Corrected variable name
    finally:
        if scraper:
            await scraper.async_close() # Ensure client is closed


async def main():
    parser = argparse.ArgumentParser(description="Generate mock subtitle data for iSubRip testing.")
    parser.add_argument(
        "-s", "--scraper",
        required=True,
        nargs="+",
        help="ID(s) of the scraper(s) to use (e.g., 'itunes', 'appletv')."
    )
    parser.add_argument(
        "-i", "--urls", # Renamed from --ids
        required=True,
        nargs="+",
        metavar="URL",
        help="Full URL(s) of the media item(s) to fetch data for (e.g., iTunes movie URL)."
    )
    parser.add_argument(
        "-l", "--languages",
        nargs="*",
        default=None,
        help="Optional language codes to filter subtitles (e.g., 'en', 'es'). Fetches all if omitted."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "mock_data",
        help="Base directory to save mock data."
    )
    # TODO: Add argument for config file path?

    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Output directory: {output_dir.resolve()}")

    # TODO: Load Config if needed

    tasks = []
    for scraper_id in args.scraper:
        available_scrapers = [s.id for s in ScraperFactory.get_scraper_classes()]
        if scraper_id not in available_scrapers:
            log.error(f"Unknown scraper ID: '{scraper_id}'. Available: {available_scrapers}")
            continue

        for media_url in args.urls: # Use args.urls
            tasks.append(
                fetch_and_save_mock_data(
                    scraper_id=scraper_id,
                    media_url=media_url, # Pass URL
                    output_base_dir=output_dir,
                    languages=args.languages,
                )
            )

    if tasks:
        log.info(f"Starting data fetch for {len(tasks)} items...")
        await asyncio.gather(*tasks)
        log.info("Mock data generation complete.")
    else:
        log.warning("No valid scraper/ID combinations to process.")


if __name__ == "__main__":
    # Ensure temp dir exists
    TEMP_FOLDER_PATH.mkdir(parents=True, exist_ok=True)
    asyncio.run(main())