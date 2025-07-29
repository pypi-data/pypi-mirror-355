import json
from pathlib import Path
from typing import Dict, Any, Optional

class CacheManager:
    """
    Manages a local file-based cache for storing AI-generated commit summaries.
    The cache is a simple JSON file stored in the user's home directory.
    """
    def __init__(self, repo_path: str):
        """
        Initializes the CacheManager.

        The cache file is specific to the repository being analyzed.

        Args:
            repo_path: The file path to the Git repository, used to create a unique cache file name.
        """
        repo_name = Path(repo_path).name
        cache_dir = Path.home() / '.gitanalytics' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / f'{repo_name}_cache.json'
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Loads the cache from the JSON file if it exists."""
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from the cache.

        Args:
            key: The key for the item to retrieve (e.g., a commit hash).

        Returns:
            The cached value, or None if the key is not found.
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any):
        """
        Sets an item in the cache and saves it to the file.

        Args:
            key: The key for the item to set (e.g., a commit hash).
            value: The value to store in the cache.
        """
        self._cache[key] = value
        self._save_cache()

    def _save_cache(self):
        """Saves the current state of the cache to the JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=4)
        except IOError as e:
            print(f"Warning: Could not save cache file: {e}")

    def clear(self):
        """Clears the cache and deletes the cache file."""
        self._cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
