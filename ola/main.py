import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse

from .database_manager import DatabaseManager
from .lang import LANGUAGE_MAP, LANGUAGE_MAP_REVERSE, LANGUAGE_NAMES
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


@app.get("/search/{path:path}")
async def proxy_old_api(
    path: str,
    request: Request,
    apiKey: str = Query(..., description="OpenSubtitles API Key"),
):
    """
    Emulate the old OpenSubtitles REST API while using the new JSON API under the hood.
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

    # Check cache first
    cache_key = db.generate_cache_key(f"tt{imdb_id}", season, episode, new_lang)
    cached_result = db.get_search_cache(cache_key)

    if cached_result:
        log.info(f"Returning cached result for {cache_key}")
        return cached_result

    # Call the new API with redirect following
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
                raise HTTPException(status_code=r.status_code, detail="Failed to fetch from new API")

        except httpx.HTTPStatusError as e:
            log.error(f"HTTP error occurred: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            log.error(f"Request error occurred: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to OpenSubtitles API")

    new_data = r.json()
    results = []

    if "data" not in new_data:
        return []

    # Get base URL for download links
    base_url = str(request.url).split("/search/")[0]

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

        results.append(
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
            }
        )

    # Cache the results
    db.set_search_cache(cache_key, results)

    return results


@app.get("/download/file/{file_id}")
async def download_file(file_id: str):
    """
    Serve subtitle file from local storage
    """
    # Get file info from database
    file_info = db.get_file_info(file_id)

    if file_info and Path(file_info["file_path"]).exists():
        # Serve the original SRT file
        return FileResponse(
            file_info["file_path"],
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={file_id}.srt",
            },
        )

    raise HTTPException(status_code=404, detail="Subtitle file not found")


@app.get("/download/zip/{file_id}")
async def download_zip(file_id: str):
    """
    Serve zipped subtitle file from local storage
    """
    # Get file info from database
    file_info = db.get_file_info(file_id)

    if file_info and Path(file_info["zip_path"]).exists():
        # Serve the zipped file
        return FileResponse(
            file_info["zip_path"],
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={file_id}.zip",
            },
        )

    raise HTTPException(status_code=404, detail="Zipped subtitle file not found")
