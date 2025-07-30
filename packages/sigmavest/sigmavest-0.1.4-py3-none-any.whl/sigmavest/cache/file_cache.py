import os
import time
import pickle
from typing import Optional
import glob


class NotInCacheError(Exception):
    """Exception raised when a cache entry is not found."""

    pass


class FileCache:
    """A simple file-based cache system that stores and retrieves data using a key-value pair.

    The cache is designed to be used for storing data that can be expensive to compute or retrieve,
    allowing for faster access on subsequent requests.
    
    The cache supports organizing entries by topics, allowing for better organization and retrieval of data.
    
    The cache is implemented using the file system, where each cache entry is stored in a separate file.
    The cache files are stored in a specified directory and can be organized by topics.
    The cache files are named using a specified format, and the cache can be vacuumed to remove expired entries.
    The cache uses a time-to-live (TTL) value to determine if a cache entry is still valid.

    Example usage:
        Here is an example of how to use the `FileCache` class to cache data from the `yfinance` library:

        ```python
        import yfinance as yf
        from sigmavest.cache.file_cache import FileCache

        ticker_symbol = "AAPL"

        cache = FileCache(cache_dir="yfinance-cache", ttl=3600, topic=ticker_symbol)
        # Vacuum expired cache files
        cache.vacuum()

        ticker = yf.Ticker(ticker_symbol)

        hist = cache.get("history", not_found_callback=lambda: ticker.history(period="5y"))
        print(hist)
        ```
    """
    default_topic: str = "default"
    filename_format = "{topic}_{key}.cache"

    def __init__(self, cache_dir: str, ttl: int = 3600, topic: Optional[str] = None):
        """
        Args:
            cache_dir (str): Directory to store cache files.
            ttl (int): Time-to-live for cache files in seconds (default: 1 hour = 3600 seconds).
            topic (Optional[str]): Default topic to use if not specified in other methods.
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.default_topic = topic or self.default_topic
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str, topic: Optional[str] = None) -> str:
        topic = topic or self.default_topic
        filename = self.filename_format.format(topic=topic, key=key)
        filename = self._sanitize_filename(filename)
        return os.path.join(self.cache_dir, filename)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize the given filename by removing or replacing invalid characters.

        Args:
            filename (str): The filename to sanitize.

        Returns:
            str: A sanitized filename.
        """
        return "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)

    def _is_cache_valid(self, cache_path: str) -> bool:
        if not os.path.exists(cache_path):
            return False
        return time.time() - os.path.getmtime(cache_path) < self.ttl

    def get(self, key: str, topic: Optional[str] = None, not_found_callback=None, force: bool = False):
        """
        Retrieve data from the cache for a given key and optional topic.
        If the cache entry is not found or expired, or if force=True, use the not_found_callback to retrieve the value.

        Args:
            key (str): The key of the cache entry.
            topic (Optional[str]): The topic of the cache entry (default: None).
            not_found_callback (callable, optional): A function to call to retrieve the value if not found in cache.
            force (bool): If True, bypass the cache and use the not_found_callback to retrieve fresh data (default: False).

        Raises:
            NotInCacheError: If the cache entry is not found or expired and no callback is provided.

        Returns:
            The cached data or the value retrieved by the callback.
        """
        cache_path = self._get_cache_path(key, topic)
        if force or not self._is_cache_valid(cache_path):
            if not_found_callback is None:
                raise NotInCacheError(
                    f"Cache entry for key '{key}' and topic '{topic or self.default_topic}' not found or expired."
                )
            # Retrieve the value using the callback and store it in the cache
            data = not_found_callback()
            self.put(key, data, topic)
            return data

        with open(cache_path, "rb") as f:
            return pickle.load(f)

    def put(self, key: str, data, topic: Optional[str] = None):
        """
        Store data in the cache for a given key and optional topic.

        Args:
            key (str): The key of the cache entry.
            data: The data to cache.
            topic (Optional[str]): The topic of the cache entry (default: None).
        """
        cache_path = self._get_cache_path(key, topic)
        with open(cache_path, "wb") as f:
            pickle.dump(data, f)

    def vacuum(self):
        """
        Remove all expired cache files from the cache directory that match the cache file name format.
        """
        glob_pattern = self.filename_format.format(topic="*", key="*")
        glob_path = os.path.join(self.cache_dir, glob_pattern)
        for cache_path in glob.glob(glob_path):
            if not self._is_cache_valid(cache_path):
                os.remove(cache_path)
