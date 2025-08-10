import redis
from datetime import timedelta
from functools import wraps
import json
from flask import request, jsonify
import logging
from time import sleep
import os
import zlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0, max_retries=3, compression_threshold=10240):
        self._is_connected = False
        self.default_ttl = int(timedelta(minutes=10).total_seconds())  # Ensure integer
        self.max_retries = max_retries
        self.host = os.getenv('REDIS_HOST', host)
        self.port = int(os.getenv('REDIS_PORT', port))
        self.db = db
        self.compression_threshold = compression_threshold  # 10KB default
        
        # Initialize with connection retries
        self.client = self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection with retries"""
        retry_count = 0
        last_exception = None
        
        while retry_count < self.max_retries:
            try:
                client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=False,  # Work with bytes
                    socket_connect_timeout=2,
                    socket_timeout=5,
                    health_check_interval=30,
                    retry_on_timeout=True,
                    max_connections=20
                )
                if client.ping():
                    self._is_connected = True
                    logger.info(f"✅ Redis connection established to {self.host}:{self.port}")
                    return client
            except (redis.ConnectionError, redis.TimeoutError, redis.AuthenticationError) as e:
                last_exception = e
                retry_count += 1
                wait_time = min(2 ** retry_count, 10)
                logger.warning(f"⚠️ Redis connection failed (attempt {retry_count}/{self.max_retries}): {str(e)}")
                if retry_count < self.max_retries:
                    logger.info(f"🕒 Retrying in {wait_time} seconds...")
                    sleep(wait_time)
        
        self._is_connected = False
        logger.error(f"❌ Failed to connect to Redis after {self.max_retries} attempts")
        return None

    def make_cache_key(self):
        """Generate cache key from request path and query params"""
        args = dict(request.args)
        return f"cache:{request.path}:{hash(frozenset(args.items()))}"

    def _compress_data(self, data):
        """Compress data if it exceeds threshold"""
        if len(data) > self.compression_threshold:
            compressed = zlib.compress(data)
            return b'COMPRESSED:' + compressed
        return data

    def _decompress_data(self, data):
        """Decompress data if it's compressed"""
        if data.startswith(b'COMPRESSED:'):
            return zlib.decompress(data[11:])
        return data

    def _safe_cache_operation(self, operation, *args, **kwargs):
        """Wrapper for safe Redis operations"""
        try:
            if not self._is_connected:
                return None
            return operation(*args, **kwargs)
        except redis.RedisError as e:
            logger.error(f"Redis operation failed: {str(e)}")
            self._is_connected = False  # Mark as disconnected
            return None

    def cache_response(self, ttl=None):
        """Decorator to cache route responses with compression support"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not self._is_connected:
                    return f(*args, **kwargs)
                
                cache_key = self.make_cache_key()
                
                # Try to get cached response
                cached = self._safe_cache_operation(self.client.get, cache_key)
                if cached:
                    try:
                        decompressed = self._decompress_data(cached);
                        print(decompressed);
                        return jsonify(json.loads(decompressed.decode('utf-8')))
                    except Exception as e:
                        logger.error(f"Cache decompress/deserialize error: {str(e)}")
                
                # Generate fresh response
                response = f(*args, **kwargs)
                
                # Cache successful responses
                if response.status_code == 200:
                    try:
                        data = response.get_data()
                        compressed = self._compress_data(data)
                        actual_ttl = int(ttl) if ttl is not None else self.default_ttl
                        
                        self._safe_cache_operation(
                            self.client.setex,
                            cache_key,
                            actual_ttl,
                            compressed
                        )
                    except Exception as e:
                        logger.error(f"Cache compress/set error: {str(e)}")
                
                return response
            return wrapper
        return decorator

# Initialize cache instance
cache = RedisCache(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    compression_threshold=10240  # Compress responses >10KB
)