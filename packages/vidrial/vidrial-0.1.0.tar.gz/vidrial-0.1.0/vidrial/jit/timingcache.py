import os
import yaml
import logging
from typing import Callable

logger = logging.getLogger(__name__)
DEFAULT_TIMING_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.timing_cache')


class ConfigTimingCache:
    """A disk-backed cache for storing config timing results.
    
    The cache stores entries of the form:
    {
        hash_key: [
            {
                "timings": [      # List sorted by time (ascending)
                    {
                        "config": {...}, # Configuration that was tested
                        "time": float,   # Timing result
                        "std": float,    # Standard deviation of the timing result
                        "n": int,        # Number of runs
                    },
                    ...
                ]
            },
            ...  # Multiple arguments can hash to the same key
        ]
    }
    
    The cache itself is kept sorted by the best (lowest) timing of each entry,
    allowing fast access to optimal configurations.
    """
    
    def __init__(
        self, 
        fn: str, 
        hash_fn: Callable[[dict], str],
        root: str | None = None, 
        size: int | None = None,
        strict: bool = False
    ):
        """ Args:
                fn: Name of the function being cached
                hash_fn: Function that converts an arguments dict to a string hash
                root: Root directory for cache files. Defaults to .timing_cache/
                size: Maximum number of entries in the cache. Defaults to None (unlimited)
                strict: If True, verify cache is properly sorted on load
        """
        self.root = root or DEFAULT_TIMING_ROOT
        self.location = os.path.join(self.root, f"{fn}.yaml")
        self.fn = fn
        self.size = size
        self.hash_fn = hash_fn
        self._cache: dict[str, list[dict]] = {}
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.location), exist_ok=True)
        
        # Load existing cache if it exists
        if os.path.exists(self.location):
            with open(self.location, 'r') as f:
                loaded_data = yaml.load(f, yaml.Loader)
                if loaded_data is not None:
                    self._cache = loaded_data
                else:
                    self._cache = {}
        else:
            self._cache = {}

        if strict:
            self._verify_sorting()

    def _verify_sorting(self):
        """Verify that cache entries and their timings are properly sorted."""
        # Check that each timings list is sorted
        for k, entries in self._cache.items():
            for entry in entries:
                timings = entry["timings"]
                sorted_timings = sorted(timings, key=lambda x: x["time"])
                if timings != sorted_timings:
                    raise ValueError(f"Timings list not sorted for key {k}")
            entry_best_times = [entry["timings"][0]["time"] for entry in entries]
            if not all(entry_best_times[i] <= entry_best_times[i+1] for i in range(len(entry_best_times) - 1)):
                raise ValueError("Cache entries not sorted by best timing")
    
    def __getitem__(self, arguments: dict) -> dict:
        """Get the best performing config for the given input arguments.
        
        Args:
            arguments: Input arguments to look up
            
        Returns:
            The config with the lowest timing for this input arguments
        """
        key = self.hash_fn(arguments)
        return self._cache[key][0]["timings"][0]["config"]
    
    def __contains__(self, arguments: dict) -> bool:
        key = self.hash_fn(arguments)
        if key not in self._cache:
            logger.debug(f"Cache miss for {self.fn} with {key=}")
            return False
        logger.debug(f"Cache hit for {self.fn} with {key=}")
        return True

    def __len__(self) -> int:
        return len(self._cache)

    def update(self, arguments: dict, timings: list[dict]):
        """Update cache with new timings for arguments.
        
        Args:
            arguments: The input arguments
            timings: List of dicts, each containing:
                    - config: Dict of configuration parameters
                    - time: Float timing result
                    
        The entry will be inserted into the cache maintaining the sort order
        by best timing. The timings list itself will also be sorted by time.
        """
        key = self.hash_fn(arguments)
        
        # Sort timings by time
        sorted_timings = sorted(timings, key=lambda x: x["time"])
        
        entry = {"timings": sorted_timings}
        
        if key in self._cache:
            self._cache[key].append(entry)
        else:
            self._cache[key] = [entry]

        self._cache[key] = sorted(self._cache[key], key=lambda x: x["timings"][0]["time"])
        
        # Enforce size limit if needed
        while self.size is not None and len(self) > self.size:
            self._cache.popitem()
            
        # Save to disk, ensuring sorted order is preserved
        try:
            with open(self.location, 'w') as f:
                yaml.dump(self._cache, f)
        except Exception as e:
            logger.warning(f"Failed to save cache to {self.location}: {e}")

    def remove(self):
        """Remove the cache file from disk."""
        if self.location is None:
            raise ValueError("Cache location is not set")
        os.remove(self.location)

    def store(self, path: str):
        """Store the cache to a file."""
        with open(path, 'w') as f:
            yaml.dump(self._cache, f)

    def to_df(self):
        """Convert the cache to a pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self._cache)