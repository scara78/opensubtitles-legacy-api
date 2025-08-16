import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import polars as pl
from .logger import logger as log


class DatabaseManager:
    def __init__(self, storage_dir: str = "subtitles", data_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # CSV file paths
        self.subtitles_csv = self.data_dir / "subtitles.csv"
        self.files_csv = self.data_dir / "files.csv"
        self.search_cache_csv = self.data_dir / "search_cache.csv"

        # In-memory DataFrames for fast access
        self._subtitles_df = None
        self._files_df = None
        self._search_cache_df = None

        self._load_databases()

    def _load_databases(self):
        """Load databases from CSV files"""
        # Define schema to ensure key is always string
        schema = {"key": pl.String, "value": pl.String}

        # Load subtitles
        if Path(self.subtitles_csv).exists():
            self._subtitles_df = pl.read_csv(self.subtitles_csv, schema=schema)
        else:
            self._subtitles_df = pl.DataFrame({"key": [], "value": []}, schema=schema)
            self._subtitles_df.write_csv(self.subtitles_csv)

        # Load files
        if Path(self.files_csv).exists():
            self._files_df = pl.read_csv(self.files_csv, schema=schema)
        else:
            self._files_df = pl.DataFrame({"key": [], "value": []}, schema=schema)
            self._files_df.write_csv(self.files_csv)

        # Load search cache
        if Path(self.search_cache_csv).exists():
            self._search_cache_df = pl.read_csv(self.search_cache_csv, schema=schema)
        else:
            self._search_cache_df = pl.DataFrame({"key": [], "value": []}, schema=schema)
            self._search_cache_df.write_csv(self.search_cache_csv)

    def _save_subtitles(self):
        """Save subtitles DataFrame to CSV"""
        self._subtitles_df.write_csv(self.subtitles_csv)

    def _save_files(self):
        """Save files DataFrame to CSV"""
        self._files_df.write_csv(self.files_csv)

    def _save_search_cache(self):
        """Save search cache DataFrame to CSV"""
        self._search_cache_df.write_csv(self.search_cache_csv)

    def generate_cache_key(self, imdb_id: str, season: str, episode: str, language: str) -> str:
        """Generate a cache key for search results"""
        return hashlib.md5(f"{imdb_id}:{season}:{episode}:{language}".encode()).hexdigest()

    def get_search_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        # Use Polars filter for fast lookup
        result = self._search_cache_df.filter(pl.col("key") == cache_key)

        if result.height > 0:
            cache_entry = json.loads(result.select("value").item())
            # Check if cache is still valid (24 hours)
            if time.time() - cache_entry["timestamp"] < 86400:
                return cache_entry["data"]
            else:
                # Remove expired cache
                self._search_cache_df = self._search_cache_df.filter(pl.col("key") != cache_key)
                self._save_search_cache()
        return None

    def set_search_cache(self, cache_key: str, data: Dict[str, Any]):
        """Cache search results"""
        cache_entry = {"data": data, "timestamp": time.time()}
        cache_json = json.dumps(cache_entry, ensure_ascii=False)

        # Remove existing entry if it exists
        self._search_cache_df = self._search_cache_df.filter(pl.col("key") != cache_key)

        # Add new entry
        new_row = pl.DataFrame([{"key": cache_key, "value": cache_json}])
        self._search_cache_df = pl.concat([self._search_cache_df, new_row])
        self._save_search_cache()

    def store_subtitle_info(self, file_id: str, subtitle_id: str, subtitle_info: Dict[str, Any]):
        """Store subtitle metadata"""
        subtitle_data = {
            **subtitle_info,
            "file_id": file_id,
            "stored_at": time.time(),
        }
        subtitle_json = json.dumps(subtitle_data, ensure_ascii=False)

        # Remove existing entry if it exists
        self._subtitles_df = self._subtitles_df.filter(pl.col("key") != subtitle_id)

        # Add new entry
        new_row = pl.DataFrame([{"key": subtitle_id, "value": subtitle_json}])
        self._subtitles_df = pl.concat([self._subtitles_df, new_row])
        self._save_subtitles()

    def store_file_info(self, file_id: str, file_path: str, zip_path: str, original_filename: str):
        """Store file information"""
        file_data = {
            "file_path": file_path,
            "zip_path": zip_path,
            "original_filename": original_filename,
            "stored_at": time.time(),
        }
        file_json = json.dumps(file_data, ensure_ascii=False)

        # Remove existing entry if it exists
        self._files_df = self._files_df.filter(pl.col("key") != file_id)

        # Add new entry
        new_row = pl.DataFrame([{"key": file_id, "value": file_json}])
        self._files_df = pl.concat([self._files_df, new_row])
        self._save_files()

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        result = self._files_df.filter(pl.col("key") == file_id)
        if result.height > 0:
            return json.loads(result.select("value").item())
        return None

    def get_subtitle_info(self, subtitle_id: str) -> Optional[Dict[str, Any]]:
        """Get subtitle information"""
        result = self._subtitles_df.filter(pl.col("key") == subtitle_id)
        if result.height > 0:
            return json.loads(result.select("value").item())
        return None

    def file_exists(self, file_id: str) -> bool:
        """Check if file is already downloaded and stored"""
        file_info = self.get_file_info(file_id)
        if file_info:
            file_path = Path(file_info["file_path"])
            zip_path = Path(file_info["zip_path"])
            return file_path.exists() and zip_path.exists()
        return False

    def get_file_path(self, file_id: str, extension: str = ".srt") -> str:
        """Generate file path for storing subtitle"""
        return str(self.storage_dir / f"{file_id}.srt")

    def get_zip_path(self, file_id: str, extension: str = ".srt") -> str:
        """Generate zip file path for storing compressed subtitle"""
        return str(self.storage_dir / f"{file_id}.zip")

    def cleanup_old_files(self, max_age_days: int = 30):
        """Clean up old cached files"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        # Get all expired files using vectorized operations
        files_with_data = []
        for row in self._files_df.iter_rows(named=True):
            file_data = json.loads(row["value"])
            files_with_data.append(
                {
                    "key": row["key"],
                    "file_path": file_data["file_path"],
                    "zip_path": file_data["zip_path"],
                    "stored_at": file_data["stored_at"],
                }
            )

        files_to_remove = []
        for file_entry in files_with_data:
            if current_time - file_entry["stored_at"] > max_age_seconds:
                # Remove physical files
                try:
                    Path(file_entry["file_path"]).unlink(missing_ok=True)
                    Path(file_entry["zip_path"]).unlink(missing_ok=True)
                    files_to_remove.append(file_entry["key"])
                except Exception as e:
                    log.error(f"Error removing old file {file_entry['key']}: {e}")

        # Remove from database using vectorized operations
        if files_to_remove:
            self._files_df = self._files_df.filter(~pl.col("key").is_in(files_to_remove))
            self._save_files()

        # Clean up old search cache using vectorized operations
        cache_with_data = []
        for row in self._search_cache_df.iter_rows(named=True):
            cache_data = json.loads(row["value"])
            cache_with_data.append({"key": row["key"], "timestamp": cache_data["timestamp"]})

        cache_to_remove = []
        for cache_entry in cache_with_data:
            if current_time - cache_entry["timestamp"] > max_age_seconds:
                cache_to_remove.append(cache_entry["key"])

        if cache_to_remove:
            self._search_cache_df = self._search_cache_df.filter(~pl.col("key").is_in(cache_to_remove))
            self._save_search_cache()

        if files_to_remove or cache_to_remove:
            log.info(f"Cleaned up {len(files_to_remove)} files and {len(cache_to_remove)} cache entries")

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        return {
            "subtitles_count": self._subtitles_df.height,
            "files_count": self._files_df.height,
            "cache_count": self._search_cache_df.height,
        }

    def reload_databases(self):
        """Reload databases from CSV files (useful for external updates)"""
        self._load_databases()
