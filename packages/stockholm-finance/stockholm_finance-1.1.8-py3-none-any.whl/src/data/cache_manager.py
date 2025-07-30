#!/usr/bin/env python3
"""
Intelligent caching system for Stockholm
Reduces API calls by implementing smart caching strategies
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class CacheManager:
    """Intelligent cache manager with different TTL strategies for different data types"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache TTL (Time To Live) strategies in minutes
        # These values balance data freshness with API rate limits and performance
        self.cache_ttl = {
            "news": 15,  # News updates every 15 minutes - frequent enough for timely analysis
            "prices": 5,  # Prices update every 5 minutes - near real-time for active trading
            "company_names": 1440,  # Company names cache for 24 hours - rarely change
            "market_data": 10,  # Market indices every 10 minutes - important for market overview
            "policy_news": 30,  # Government news every 30 minutes - less frequent than market news
            "analyst_data": 60,  # Analyst recommendations every hour - change infrequently
            "ticker_info": 240,  # Basic ticker info every 4 hours - fundamental data changes slowly
            "earnings": 1440,  # Earnings data cache for 24 hours - quarterly updates only
        }

        # Request tracking for rate limiting
        self.request_log_file = self.cache_dir / "request_log.json"
        self.load_request_log()

    def load_request_log(self):
        """Load request tracking log"""
        try:
            if self.request_log_file.exists():
                with open(self.request_log_file, "r") as f:
                    self.request_log = json.load(f)
            else:
                self.request_log = {}
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            self.request_log = {}

    def save_request_log(self):
        """Save request tracking log"""
        try:
            with open(self.request_log_file, "w") as f:
                json.dump(self.request_log, f)
        except (OSError, PermissionError):
            pass

    def track_request(self, api_type: str, endpoint: str):
        """Track API requests for rate limiting analysis"""
        now = datetime.now().isoformat()
        key = f"{api_type}_{endpoint}"

        if key not in self.request_log:
            self.request_log[key] = []

        self.request_log[key].append(now)

        # Keep only last 24 hours of requests
        cutoff = datetime.now() - timedelta(hours=24)
        self.request_log[key] = [
            req for req in self.request_log[key] if datetime.fromisoformat(req) > cutoff
        ]

        self.save_request_log()

    def get_request_stats(self) -> Dict[str, int]:
        """Get request statistics for the last 24 hours"""
        stats = {}
        cutoff = datetime.now() - timedelta(hours=24)

        for key, requests in self.request_log.items():
            recent_requests = [
                req for req in requests if datetime.fromisoformat(req) > cutoff
            ]
            stats[key] = len(recent_requests)

        return stats

    def _get_cache_key(self, data_type: str, identifier: str) -> str:
        """Generate cache key"""
        return f"{data_type}_{hashlib.md5(identifier.encode()).hexdigest()}"

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.cache"

    def is_cache_valid(self, data_type: str, identifier: str) -> bool:
        """Check if cached data is still valid"""
        cache_key = self._get_cache_key(data_type, identifier)
        cache_file = self._get_cache_file(cache_key)

        if not cache_file.exists():
            return False

        # Check TTL
        ttl_minutes = self.cache_ttl.get(data_type, 60)
        cutoff_time = datetime.now() - timedelta(minutes=ttl_minutes)

        try:
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            return file_time > cutoff_time
        except (OSError, ValueError):
            return False

    def get_cached_data(self, data_type: str, identifier: str) -> Optional[Any]:
        """Get cached data if valid"""
        if not self.is_cache_valid(data_type, identifier):
            return None

        cache_key = self._get_cache_key(data_type, identifier)
        cache_file = self._get_cache_file(cache_key)

        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except (OSError, pickle.PickleError, EOFError):
            return None

    def cache_data(self, data_type: str, identifier: str, data: Any) -> None:
        """Cache data"""
        cache_key = self._get_cache_key(data_type, identifier)
        cache_file = self._get_cache_file(cache_key)

        try:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"⚠️ Failed to cache {data_type} for {identifier}: {e}")

    def get_or_fetch(
        self, data_type: str, identifier: str, fetch_function, *args, **kwargs
    ):
        """Get cached data or fetch new data"""
        # Try cache first
        cached_data = self.get_cached_data(data_type, identifier)
        if cached_data is not None:
            return cached_data, True  # True indicates cache hit

        # Fetch new data
        try:
            new_data = fetch_function(*args, **kwargs)
            self.cache_data(data_type, identifier, new_data)
            self.track_request(data_type, identifier)
            return new_data, False  # False indicates cache miss
        except Exception as e:
            print(f"⚠️ Failed to fetch {data_type} for {identifier}: {e}")
            return None, False

    def batch_get_or_fetch(
        self,
        data_type: str,
        identifiers: List[str],
        fetch_function,
        batch_size: int = 10,
    ):
        """Efficiently handle batch requests with caching"""
        results = {}
        cache_hits = 0
        cache_misses = []

        # Check cache for all identifiers
        for identifier in identifiers:
            cached_data = self.get_cached_data(data_type, identifier)
            if cached_data is not None:
                results[identifier] = cached_data
                cache_hits += 1
            else:
                cache_misses.append(identifier)

        # Fetch missing data in batches
        if cache_misses:
            for i in range(0, len(cache_misses), batch_size):
                batch = cache_misses[i : i + batch_size]
                try:
                    batch_results = fetch_function(batch)

                    # Cache individual results
                    for identifier in batch:
                        if identifier in batch_results:
                            self.cache_data(
                                data_type, identifier, batch_results[identifier]
                            )
                            results[identifier] = batch_results[identifier]
                            self.track_request(data_type, identifier)

                except Exception as e:
                    print(f"⚠️ Batch fetch failed for {data_type}: {e}")

        print(
            f"📊 Cache performance for {data_type}: {cache_hits} hits, {len(cache_misses)} misses"
        )
        return results

    def clear_cache(
        self, data_type: Optional[str] = None, older_than_hours: Optional[int] = None
    ):
        """Clear cache files"""
        if older_than_hours:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        for cache_file in self.cache_dir.glob("*.cache"):
            should_delete = False

            if data_type:
                # Delete specific data type
                if cache_file.name.startswith(f"{data_type}_"):
                    should_delete = True
            elif older_than_hours:
                # Delete old files
                try:
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        should_delete = True
                except (OSError, ValueError):
                    should_delete = True
            else:
                # Delete all
                should_delete = True

            if should_delete:
                try:
                    cache_file.unlink()
                except OSError:
                    pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "cache_files": len(list(self.cache_dir.glob("*.cache"))),
            "cache_size_mb": sum(
                f.stat().st_size for f in self.cache_dir.glob("*.cache")
            )
            / (1024 * 1024),
            "request_stats": self.get_request_stats(),
            "cache_ttl": self.cache_ttl,
        }
        return stats


# Global cache manager instance
cache_manager = CacheManager()
