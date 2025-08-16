import os
import re
import zipfile
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse

from .database_manager import DatabaseManager
from .lang import LANGUAGE_MAP, LANGUAGE_MAP_REVERSE, LANGUAGE_NAMES, SUBDL_LANGUAGE_MAP
from .logger import logger as log

load_dotenv()

IS_DEVELOPMENT = os.getenv("ENVIRONMENT", "production") == "development"
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

app = FastAPI(debug=IS_DEVELOPMENT)

# Initialize database manager
db = DatabaseManager()

OLD_API_PATTERN = re.compile(r"/search/episode-(\d+)/imdbid-tt(\d+)/season-(\d+)/sublanguageid-(\w+)")

# Pattern for movie searches without season/episode
MOVIE_API_PATTERN = re.compile(r"/search/imdbid-tt(\d+)/sublanguageid-(\w+)")

# SubDL API configuration
SUBDL_BASE_URL = "https://api.subdl.com/api/v1/subtitles"
SUBDL_DOWNLOAD_PREFIX = "https://dl.subdl.com"


async def download_and_store_subtitle(file_id: str, original_filename: str, api_key: str, user_agent: str) -> bool:
    """Download subtitle from OpenSubtitles and store it locally"""
    if db.file_exists(file_id):
        return True  # Already downloaded

    url = "https://api.opensubtitles.com/api/v1/download"

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        try:
            # Get download link
            r = await client.post(
                url,
                headers={
                    "Api-Key": api_key,
                    "User-Agent": user_agent,
                    "Content-Type": "application/json",
                },
                json={"file_id": int(file_id)},
            )

            if r.status_code != 200:
                log.error(f"Failed to get download link for file {file_id}: {r.status_code}")
                return False

            download_data = r.json()
            download_link = download_data.get("link")

            if not download_link:
                log.error(f"No download link received for file {file_id}")
                return False

            # Download the actual file
            file_response = await client.get(download_link)

            if file_response.status_code != 200:
                log.error(f"Failed to download file {file_id}: {file_response.status_code}")
                return False

            content = file_response.content

            # Determine file extension from original filename
            # Always use .srt for consistency
            ext = ".srt"

            # Store original file
            file_path = db.get_file_path(file_id, ext)
            with open(file_path, "wb") as f:
                f.write(content)

            # Store zipped version
            zip_path = db.get_zip_path(file_id, ext)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(f"{file_id}.srt", content)

            # Store file info in database
            db.store_file_info(file_id, file_path, zip_path, original_filename)

            log.info(f"Successfully downloaded and stored file {file_id}")
            return True

        except Exception as e:
            log.error(f"Error downloading file {file_id}: {e}")
            return False


async def download_and_store_subdl_subtitle(file_id: str, download_url: str, original_filename: str, user_agent: str) -> bool:
    """Download subtitle from SubDL and store it locally"""
    if db.file_exists(file_id):
        return True  # Already downloaded

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        try:
            # Download the file directly from SubDL
            file_response = await client.get(download_url, headers={"User-Agent": user_agent})

            if file_response.status_code != 200:
                log.error(f"Failed to download SubDL file {file_id}: {file_response.status_code}")
                return False

            content = file_response.content

            # Handle different content types
            content_type = file_response.headers.get("content-type", "").lower()

            # If it's a zip file, extract the content
            if "zip" in content_type or original_filename.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                        # Get the first .srt file in the zip
                        srt_files = [name for name in zip_file.namelist() if name.lower().endswith(".srt")]
                        if srt_files:
                            content = zip_file.read(srt_files[0])
                        else:
                            log.error(f"No .srt file found in SubDL zip {file_id}")
                            return False
                except zipfile.BadZipFile:
                    log.error(f"Invalid zip file from SubDL {file_id}")
                    return False

            # Store original file
            ext = ".srt"
            file_path = db.get_file_path(file_id, ext)
            with open(file_path, "wb") as f:
                f.write(content)

            # Store zipped version
            zip_path = db.get_zip_path(file_id, ext)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(f"{file_id}.srt", content)

            # Store file info in database
            db.store_file_info(file_id, file_path, zip_path, original_filename)

            log.info(f"Successfully downloaded and stored SubDL file {file_id}")
            return True

        except Exception as e:
            log.error(f"Error downloading SubDL file {file_id}: {e}")
            return False


async def search_subdl_subtitles(
    subdl_api_key: str,
    imdb_id: str,
    old_lang: str,
    season: Optional[str] = None,
    episode: Optional[str] = None,
    user_agent: str = "OpenSubtitles-Legacy-API v1.0",
) -> List[Dict[str, Any]]:
    """Search SubDL API for subtitles"""
    subdl_language = SUBDL_LANGUAGE_MAP.get(old_lang)

    # Skip if language is not supported by SubDL
    if subdl_language is None:
        log.warning(f"Language {old_lang} not supported by SubDL")
        return []

    params = {
        "api_key": subdl_api_key,
        "imdb_id": f"tt{imdb_id}",
        "languages": subdl_language,
        "subs_per_page": 30,
        "comment": "1",  # Get author comments
        "releases": "1",  # Get release information
        "hi": "1",  # Get hearing impaired info
    }

    # Add season/episode if provided
    if season:
        params["season_number"] = season
    if episode:
        params["episode_number"] = episode

    # Add type parameter
    if season or episode:
        params["type"] = "tv"
    else:
        params["type"] = "movie"

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            r = await client.get(
                SUBDL_BASE_URL,
                params=params,
                headers={"User-Agent": user_agent},
            )

            if r.status_code != 200:
                log.error(f"SubDL API request failed: {r.status_code} - {r.text}")
                return []

            data = r.json()
            log.info(f"SubDL search results for IMDB {imdb_id}: status={data.get('status')}, subtitles_count={len(data.get('subtitles', []))}")

            if not data.get("status", False):
                log.warning(f"SubDL returned status=false for IMDB {imdb_id}: {data.get('error', 'Unknown error')}")
                return []

            if "subtitles" not in data:
                log.warning(f"SubDL returned no subtitles field for IMDB {imdb_id}")
                return []

            return data["subtitles"]

        except Exception as e:
            log.error(f"Error searching SubDL: {e}")
            return []


def transform_subdl_to_opensubtitles_format(
    subdl_subtitle: Dict[str, Any],
    base_url: str,
    old_lang_code: str,
    imdb_id: str,
    season: Optional[str] = None,
    episode: Optional[str] = None,
    index: int = 0,
) -> Dict[str, Any]:
    """Transform SubDL subtitle format to OpenSubtitles legacy format"""

    # Generate a unique file ID for SubDL subtitle (prefix with 'subdl_')
    subdl_url = subdl_subtitle.get("url", "")
    file_id = f"subdl_{abs(hash(subdl_url))}_{index}"

    # Create download URL
    download_url = SUBDL_DOWNLOAD_PREFIX + subdl_url if subdl_url else ""

    # Extract release name from release_name or releases list
    release_name = subdl_subtitle.get("release_name", "")
    if not release_name and subdl_subtitle.get("releases"):
        releases = subdl_subtitle.get("releases", [])
        if releases and len(releases) > 0:
            release_name = releases[0].get("release", "")

    # Get author comment
    author_comment = ""
    if subdl_subtitle.get("comment"):
        author_comment = subdl_subtitle.get("comment", "")

    # Get hearing impaired status
    hearing_impaired = "0"
    if subdl_subtitle.get("hi"):
        hearing_impaired = "1" if subdl_subtitle.get("hi") else "0"

    return {
        "MatchedBy": "imdbid",
        "IDSubMovieFile": "0",
        "MovieHash": "0",
        "MovieByteSize": "0",
        "MovieTimeMS": "0",
        "IDSubtitleFile": file_id,
        "SubFileName": subdl_subtitle.get("name", ""),
        "SubActualCD": "1",
        "SubSize": "0",
        "SubHash": "",
        "SubLastTS": "",
        "SubTSGroup": "1",
        "IDSubtitle": file_id,  # Use file_id as subtitle_id for SubDL
        "UserID": "0",
        "SubLanguageID": old_lang_code,
        "SubFormat": "srt",
        "SubSumCD": "1",
        "SubAuthorComment": author_comment,
        "SubAddDate": "",  # SubDL doesn't provide upload date
        "SubBad": "0",
        "SubRating": "0.0",
        "SubSumVotes": "0",
        "SubDownloadsCnt": "0",
        "MovieReleaseName": release_name,
        "MovieFPS": "0.000",
        "IDMovie": "0",
        "IDMovieImdb": imdb_id,
        "MovieName": "",
        "MovieNameEng": "",
        "MovieYear": "",
        "MovieImdbRating": "0.0",
        "SubFeatured": "0",
        "UserNickName": subdl_subtitle.get("author", "SubDL"),
        "SubTranslator": "",
        "ISO639": old_lang_code[:2] if old_lang_code else "en",
        "LanguageName": LANGUAGE_NAMES.get(old_lang_code, subdl_subtitle.get("lang", "English")),
        "SubComments": "0",
        "SubHearingImpaired": hearing_impaired,
        "UserRank": "",
        "SeriesSeason": str(subdl_subtitle.get("season", season or "")),
        "SeriesEpisode": str(subdl_subtitle.get("episode", episode or "")),
        "MovieKind": "tv" if season or episode else "movie",
        "SubHD": "0",
        "SeriesIMDBParent": imdb_id,
        "SubEncoding": "UTF-8",
        "SubAutoTranslation": "0",
        "SubForeignPartsOnly": "0",
        "SubFromTrusted": "0",
        "SubTSGroupHash": "",
        # Use our proxy download endpoints
        "SubDownloadLink": f"{base_url}/download/file/{file_id}",
        "ZipDownloadLink": f"{base_url}/download/zip/{file_id}",
        "SubtitlesLink": download_url,
        "QueryNumber": str(index),
        "QueryParameters": {
            "imdbid": imdb_id,
            "sublanguageid": old_lang_code,
            **({"episode": int(episode), "season": int(season)} if episode and season else {}),
        },
        "Score": 5.0 - (index * 0.01),  # Lower score than OpenSubtitles to prefer OS results
        "Provider": "SubDL",  # Add provider info
    }


@app.get("/search/{path:path}")
async def proxy_old_api(
    path: str,
    request: Request,
    apiKey: str = Query(..., description="OpenSubtitles API Key"),
    subdlKey: Optional[str] = Query(None, description="SubDL API Key (optional)"),
):
    """
    Emulate the old OpenSubtitles REST API while using the new JSON API under the hood.
    Optionally merges results from SubDL if subdlKey is provided.
    """
    if not apiKey:
        raise HTTPException(status_code=400, detail="API Key is required")

    # Get User-Agent from client request
    user_agent = request.headers.get("user-agent", "OpenSubtitles-Legacy-API v1.0")

    # Try episode pattern first
    match = OLD_API_PATTERN.match("/search/" + path)
    if match:
        episode, imdb_id, season, old_lang = match.groups()
        has_episode = True
    else:
        # Try movie pattern
        movie_match = MOVIE_API_PATTERN.match("/search/" + path)
        if movie_match:
            imdb_id, old_lang = movie_match.groups()
            episode = season = None
            has_episode = False
        else:
            raise HTTPException(status_code=400, detail="Invalid old API path format")

    new_lang = LANGUAGE_MAP.get(old_lang, old_lang)

    # Check cache first (include subdl in cache key if provided)
    cache_suffix = "_with_subdl" if subdlKey else ""
    cache_key = db.generate_cache_key(f"tt{imdb_id}", season, episode, new_lang) + cache_suffix
    cached_result = db.get_search_cache(cache_key)

    if cached_result:
        log.info(f"Returning cached result for {cache_key}")
        return cached_result

    # Get base URL for download links
    base_url = str(request.url).split("/search/")[0]

    # Start with OpenSubtitles results
    opensubtitles_results = []

    # Call the OpenSubtitles API
    url = "https://api.opensubtitles.com/api/v1/subtitles"
    params = {
        "imdb_id": f"tt{imdb_id}",
        "languages": new_lang,
    }

    # Only add season and episode if this is an episode search
    if has_episode:
        params["season_number"] = season
        params["episode_number"] = episode

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            r = await client.get(
                url,
                headers={
                    "Api-Key": apiKey,
                    "User-Agent": user_agent,
                },
                params=params,
            )

            if r.status_code != 200:
                log.warning(f"OpenSubtitles API failed with status {r.status_code}")
            else:
                new_data = r.json()

                if "data" in new_data:
                    for idx, item in enumerate(new_data["data"]):
                        attr = item.get("attributes", {})
                        feature = attr.get("feature_details", {})
                        uploader = attr.get("uploader", {})
                        files = attr.get("files", [])
                        file_entry = files[0] if files else {}

                        # Fix: Use imdb_id for episodes, keep full format
                        movie_imdb_id = str(feature.get("imdb_id", "0"))
                        parent_imdb = str(feature.get("parent_imdb_id", "0"))

                        old_lang_code = LANGUAGE_MAP_REVERSE.get(attr.get("language"), attr.get("language", "eng"))

                        file_id = str(file_entry.get("file_id", "0"))
                        subtitle_id = attr.get("subtitle_id", "")

                        # Download and store the subtitle file
                        original_filename = file_entry.get("file_name", f"{file_id}.srt")
                        await download_and_store_subtitle(file_id, original_filename, apiKey, user_agent)

                        # Store subtitle metadata
                        db.store_subtitle_info(
                            file_id,
                            subtitle_id,
                            {
                                "language": attr.get("language"),
                                "download_count": attr.get("download_count", 0),
                                "hearing_impaired": attr.get("hearing_impaired", False),
                                "hd": attr.get("hd", False),
                                "fps": attr.get("fps", 0),
                                "votes": attr.get("votes", 0),
                                "ratings": attr.get("ratings", 0),
                                "from_trusted": attr.get("from_trusted", False),
                                "foreign_parts_only": attr.get("foreign_parts_only", False),
                                "upload_date": attr.get("upload_date"),
                                "release": attr.get("release", ""),
                                "comments": attr.get("comments", ""),
                                "feature_details": feature,
                                "uploader": uploader,
                                "original_filename": original_filename,
                            },
                        )

                        opensubtitles_results.append(
                            {
                                "MatchedBy": "imdbid",
                                "IDSubMovieFile": "0",
                                "MovieHash": "0",
                                "MovieByteSize": "0",
                                "MovieTimeMS": "0",
                                "IDSubtitleFile": file_id,
                                "SubFileName": file_entry.get("file_name", ""),
                                "SubActualCD": str(file_entry.get("cd_number", 1)),
                                "SubSize": "0",
                                "SubHash": "",
                                "SubLastTS": "",
                                "SubTSGroup": "1",
                                "IDSubtitle": subtitle_id,
                                "UserID": str(uploader.get("uploader_id", "0") if uploader.get("uploader_id") else "0"),
                                "SubLanguageID": old_lang_code,
                                "SubFormat": (attr.get("format") if isinstance(attr.get("format"), str) else "srt"),
                                "SubSumCD": str(attr.get("nb_cd", len(files) or 1)),
                                "SubAuthorComment": attr.get("comments", ""),
                                "SubAddDate": (
                                    datetime.fromisoformat(attr["upload_date"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                                    if attr.get("upload_date")
                                    else ""
                                ),
                                "SubBad": "0",
                                "SubRating": str(attr.get("ratings", "0.0")),
                                "SubSumVotes": str(attr.get("votes", "0")),
                                "SubDownloadsCnt": str(attr.get("download_count", "0")),
                                "MovieReleaseName": attr.get("release", ""),
                                "MovieFPS": str(attr.get("fps", "0.000")),
                                "IDMovie": str(feature.get("feature_id", "0")),
                                "IDMovieImdb": movie_imdb_id,
                                "MovieName": feature.get("title", ""),
                                "MovieNameEng": feature.get("original_title") or feature.get("title", ""),
                                "MovieYear": str(feature.get("year", "")),
                                "MovieImdbRating": "0.0",
                                "SubFeatured": "0",
                                "UserNickName": uploader.get("name", "Anonymous"),
                                "SubTranslator": "",
                                "ISO639": old_lang_code[:2] if old_lang_code else "en",
                                "LanguageName": LANGUAGE_NAMES.get(old_lang_code, attr.get("language", "English")),
                                "SubComments": "0",
                                "SubHearingImpaired": "1" if attr.get("hearing_impaired") else "0",
                                "UserRank": uploader.get("rank", ""),
                                "SeriesSeason": str(feature.get("season_number", season or "")),
                                "SeriesEpisode": str(feature.get("episode_number", episode or "")),
                                "MovieKind": feature.get("feature_type", "episode" if has_episode else "movie").lower(),
                                "SubHD": "1" if attr.get("hd") else "0",
                                "SeriesIMDBParent": parent_imdb,
                                "SubEncoding": "UTF-8",
                                "SubAutoTranslation": "1" if attr.get("machine_translated") else "0",
                                "SubForeignPartsOnly": "1" if attr.get("foreign_parts_only") else "0",
                                "SubFromTrusted": "1" if attr.get("from_trusted") else "0",
                                "SubTSGroupHash": "",
                                # Use our proxy download endpoints
                                "SubDownloadLink": f"{base_url}/download/file/{file_id}",
                                "ZipDownloadLink": f"{base_url}/download/zip/{file_id}",
                                "SubtitlesLink": attr.get("url", ""),
                                "QueryNumber": str(idx),
                                "QueryParameters": {
                                    "imdbid": imdb_id,
                                    "sublanguageid": old_lang,
                                    **({"episode": int(episode), "season": int(season)} if has_episode else {}),
                                },
                                "Score": 10.0 - (idx * 0.01),
                                "Provider": "OpenSubtitles",  # Add provider info
                            }
                        )

        except httpx.HTTPStatusError as e:
            log.error(f"OpenSubtitles HTTP error occurred: {e}")
        except httpx.RequestError as e:
            log.error(f"OpenSubtitles request error occurred: {e}")

    # Search SubDL if API key is provided
    subdl_results = []
    if subdlKey:
        try:
            subdl_subtitles = await search_subdl_subtitles(subdlKey, imdb_id, old_lang, season, episode, user_agent)

            for idx, subdl_subtitle in enumerate(subdl_subtitles):
                # Transform SubDL format to OpenSubtitles format
                transformed_subtitle = transform_subdl_to_opensubtitles_format(
                    subdl_subtitle, base_url, old_lang, imdb_id, season, episode, len(opensubtitles_results) + idx
                )

                # Download and store SubDL subtitle
                file_id = transformed_subtitle["IDSubtitleFile"]
                download_url = SUBDL_DOWNLOAD_PREFIX + subdl_subtitle.get("url", "")
                original_filename = subdl_subtitle.get("name", f"{file_id}.srt")

                if download_url and subdl_subtitle.get("url"):
                    await download_and_store_subdl_subtitle(file_id, download_url, original_filename, user_agent)

                    # Extract release name for metadata
                    release_name = subdl_subtitle.get("release_name", "")
                    if not release_name and subdl_subtitle.get("releases"):
                        releases = subdl_subtitle.get("releases", [])
                        if releases and len(releases) > 0:
                            release_name = releases[0].get("release", "")

                    # Store SubDL subtitle metadata
                    db.store_subtitle_info(
                        file_id,
                        file_id,  # Use file_id as subtitle_id for SubDL
                        {
                            "language": subdl_subtitle.get("lang", ""),
                            "download_count": 0,
                            "hearing_impaired": bool(subdl_subtitle.get("hi", False)),
                            "hd": False,
                            "fps": 0,
                            "votes": 0,
                            "ratings": 0,
                            "from_trusted": False,
                            "foreign_parts_only": False,
                            "upload_date": "",
                            "release": release_name,
                            "comments": subdl_subtitle.get("comment", ""),
                            "feature_details": {},
                            "uploader": {"name": subdl_subtitle.get("author", "SubDL")},
                            "original_filename": original_filename,
                            "provider": "SubDL",
                            "subdl_data": subdl_subtitle,
                            "subdl_releases": subdl_subtitle.get("releases", []),
                        },
                    )

                subdl_results.append(transformed_subtitle)

        except Exception as e:
            log.error(f"Error searching SubDL: {e}")

    # Combine results (OpenSubtitles first, then SubDL)
    all_results = opensubtitles_results + subdl_results

    # Update QueryNumber for combined results
    for idx, result in enumerate(all_results):
        result["QueryNumber"] = str(idx)

    # Cache the combined results
    db.set_search_cache(cache_key, all_results)

    log.info(f"Returning {len(opensubtitles_results)} OpenSubtitles + {len(subdl_results)} SubDL results")
    return all_results


@app.get("/download/file/{file_id}")
async def download_file(file_id: str):
    """
    Serve subtitle file from local storage (supports both OpenSubtitles and SubDL)
    """
    # Get file info from database
    file_info = db.get_file_info(file_id)

    if file_info and Path(file_info["file_path"]).exists():
        # Serve the original SRT file
        filename = f"{file_id}.srt"
        # Use original filename if available and it's from SubDL
        if file_id.startswith("subdl_") and file_info.get("original_filename"):
            original_name = file_info["original_filename"]
            # Ensure it has .srt extension
            if not original_name.lower().endswith(".srt"):
                original_name = original_name.rsplit(".", 1)[0] + ".srt"
            filename = original_name

        return FileResponse(
            file_info["file_path"],
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    raise HTTPException(status_code=404, detail="Subtitle file not found")


@app.get("/download/zip/{file_id}")
async def download_zip(file_id: str):
    """
    Serve zipped subtitle file from local storage (supports both OpenSubtitles and SubDL)
    """
    # Get file info from database
    file_info = db.get_file_info(file_id)

    if file_info and Path(file_info["zip_path"]).exists():
        # Serve the zipped file
        filename = f"{file_id}.zip"
        # Use original filename if available and it's from SubDL
        if file_id.startswith("subdl_") and file_info.get("original_filename"):
            original_name = file_info["original_filename"]
            # Change extension to .zip
            filename = original_name.rsplit(".", 1)[0] + ".zip"

        return FileResponse(
            file_info["zip_path"],
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    raise HTTPException(status_code=404, detail="Zipped subtitle file not found")
