import os
import hashlib
import threading
import time
import logging
from typing import Optional, Dict, Tuple
from pathlib import Path
import json
from collections import OrderedDict

logger = logging.getLogger(__name__)

class FileCacheService:
    """    
    Features:
    - LRU cache eviction
    - Thread-safe operations
    - Configurable size limits
    - Metadata tracking
    - Automatic cleanup
    """
    
    def __init__(
        self,
        cache_dir: str = "/tmp/file_cache",
        max_cache_size_gb: float = 30.0,  # 30GB max cache size
        max_file_age_hours: int = 1,      # Files expire after 1 hour
        cleanup_threshold: float = 0.9    # Cleanup when 90% full
    ):
        self.cache_dir = Path(cache_dir)
        self.max_cache_size_bytes = int(max_cache_size_gb * 1024 * 1024 * 1024)
        self.max_file_age_seconds = max_file_age_hours * 3600
        self.cleanup_threshold = cleanup_threshold
        
        # Thread safety
        self._lock = threading.RLock()
        
        # In-memory metadata for fast access
        self._metadata: OrderedDict[str, Dict] = OrderedDict()
        self._current_size = 0
        
        # Initialize cache directory
        self._init_cache_dir()
        self._load_metadata()
        
        logger.info(f"FileCacheService initialized with cache_dir={cache_dir}, max_size={max_cache_size_gb}GB")
    
    def _init_cache_dir(self):
        """Initialize cache directory structure."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for better organization
        (self.cache_dir / "files").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
    
    def _get_cache_key(self, s3_key: str) -> str:
        """Generate a safe cache key from S3 key."""
        return hashlib.sha256(s3_key.encode()).hexdigest()
    
    def _get_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / "files" / cache_key
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get the metadata file path for a cache key."""
        return self.cache_dir / "metadata" / f"{cache_key}.json"
    
    def _load_metadata(self):
        """Load existing metadata from disk."""
        try:
            metadata_dir = self.cache_dir / "metadata"
            if not metadata_dir.exists():
                return
                
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    cache_key = metadata_file.stem
                    file_path = self._get_file_path(cache_key)
                    
                    # Check if file still exists
                    if file_path.exists():
                        # Update file size from actual file
                        metadata['size'] = file_path.stat().st_size
                        self._metadata[cache_key] = metadata
                        self._current_size += metadata['size']
                    else:
                        # Remove orphaned metadata
                        metadata_file.unlink(missing_ok=True)
                        
                except Exception as e:
                    logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
                    
            logger.info(f"Loaded {len(self._metadata)} cached files, total size: {self._current_size / (1024*1024):.1f}MB")
            
        except Exception as e:
            logger.error(f"Failed to load cache metadata: {e}")
    
    def _save_metadata(self, cache_key: str, metadata: Dict):
        """Save metadata for a cache entry."""
        try:
            metadata_path = self._get_metadata_path(cache_key)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            logger.error(f"Failed to save metadata for {cache_key}: {e}")
    
    def _cleanup_if_needed(self):
        """Cleanup old files if cache is getting full."""
        if self._current_size < (self.max_cache_size_bytes * self.cleanup_threshold):
            return
            
        logger.info("Starting cache cleanup...")
        current_time = time.time()
        removed_count = 0
        freed_space = 0
        
        # Remove expired files first
        expired_keys = []
        for cache_key, metadata in list(self._metadata.items()):
            if current_time - metadata['accessed_at'] > self.max_file_age_seconds:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            freed_space += self._remove_cached_file(cache_key)
            removed_count += 1
        
        # If still over threshold, remove LRU files
        while (self._current_size > (self.max_cache_size_bytes * 0.8) and 
               len(self._metadata) > 0):
            # Remove least recently used (first item in OrderedDict)
            cache_key = next(iter(self._metadata))
            freed_space += self._remove_cached_file(cache_key)
            removed_count += 1
        
        logger.info(f"Cache cleanup completed: removed {removed_count} files, freed {freed_space / (1024*1024):.1f}MB")
    
    def _remove_cached_file(self, cache_key: str) -> int:
        """Remove a cached file and its metadata."""
        try:
            metadata = self._metadata.pop(cache_key, {})
            file_size = metadata.get('size', 0)
            
            # Remove files
            self._get_file_path(cache_key).unlink(missing_ok=True)
            self._get_metadata_path(cache_key).unlink(missing_ok=True)
            
            self._current_size -= file_size
            return file_size
            
        except Exception as e:
            logger.error(f"Failed to remove cached file {cache_key}: {e}")
            return 0
    
    def get_cached_file(self, s3_key: str) -> Optional[bytes]:
        """
        Get a file from cache if it exists and is not expired.
        
        Args:
            s3_key: The S3 key of the file
            
        Returns:
            File content as bytes if cached, None otherwise
        """
        cache_key = self._get_cache_key(s3_key)
        
        with self._lock:
            # Check if file is in cache
            if cache_key not in self._metadata:
                return None
            
            metadata = self._metadata[cache_key]
            current_time = time.time()
            
            # Check if file is expired
            if current_time - metadata['accessed_at'] > self.max_file_age_seconds:
                self._remove_cached_file(cache_key)
                return None
            
            file_path = self._get_file_path(cache_key)
            if not file_path.exists():
                # File was removed externally, clean up metadata
                self._metadata.pop(cache_key, None)
                self._get_metadata_path(cache_key).unlink(missing_ok=True)
                return None
            
            try:
                # Read file content
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Update access time and move to end (LRU)
                metadata['accessed_at'] = current_time
                metadata['hit_count'] = metadata.get('hit_count', 0) + 1
                self._metadata.move_to_end(cache_key)
                self._save_metadata(cache_key, metadata)
                
                logger.debug(f"Cache HIT for {s3_key} (hits: {metadata['hit_count']})")
                return content
                
            except Exception as e:
                logger.error(f"Failed to read cached file {cache_key}: {e}")
                self._remove_cached_file(cache_key)
                return None
    
    def cache_file(self, s3_key: str, content: bytes) -> bool:
        """
        Cache a file to local storage.
        
        Args:
            s3_key: The S3 key of the file
            content: File content as bytes
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not content:
            return False
            
        cache_key = self._get_cache_key(s3_key)
        file_size = len(content)
        
        # Don't cache files that are too large (> 100MB)
        if file_size > 100 * 1024 * 1024:
            logger.warning(f"File {s3_key} too large to cache ({file_size / (1024*1024):.1f}MB)")
            return False
        
        with self._lock:
            # Cleanup if needed before adding new file
            self._cleanup_if_needed()
            
            # Check if we have enough space
            if self._current_size + file_size > self.max_cache_size_bytes:
                logger.warning(f"Not enough cache space for {s3_key}")
                return False
            
            try:
                file_path = self._get_file_path(cache_key)
                
                # Write file content
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Create metadata
                current_time = time.time()
                metadata = {
                    's3_key': s3_key,
                    'size': file_size,
                    'cached_at': current_time,
                    'accessed_at': current_time,
                    'hit_count': 0
                }
                
                # Update cache state
                self._metadata[cache_key] = metadata
                self._current_size += file_size
                self._save_metadata(cache_key, metadata)
                
                logger.debug(f"Cached file {s3_key} ({file_size / 1024:.1f}KB)")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cache file {s3_key}: {e}")
                # Clean up partial file
                self._get_file_path(cache_key).unlink(missing_ok=True)
                return False
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            total_hits = sum(metadata.get('hit_count', 0) for metadata in self._metadata.values())
            
            return {
                'total_files': len(self._metadata),
                'total_size_mb': self._current_size / (1024 * 1024),
                'total_size_gb': self._current_size / (1024 * 1024 * 1024),
                'max_size_gb': self.max_cache_size_bytes / (1024 * 1024 * 1024),
                'usage_percent': (self._current_size / self.max_cache_size_bytes) * 100,
                'total_hits': total_hits,
                'cache_dir': str(self.cache_dir)
            }
    
    def clear_cache(self):
        """Clear all cached files."""
        with self._lock:
            for cache_key in list(self._metadata.keys()):
                self._remove_cached_file(cache_key)
            
            logger.info("Cache cleared")


# Global cache instance
_cache_instance = None
_cache_lock = threading.Lock()

def get_cache_service() -> FileCacheService:
    """Get the global cache service instance (singleton)."""
    global _cache_instance
    
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = FileCacheService()
    
    return _cache_instance 