"""
Multi-user MCP Connection Pool with LRU cache, TTL, and background cleanup
"""

import asyncio
import hashlib
import json
import logging
import time
import weakref
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Set
from collections import OrderedDict
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about an MCP connection"""

    client: MultiServerMCPClient
    created_at: float
    last_used: float
    use_count: int = 0
    user_id: Optional[str] = None
    config_hash: str = ""

    def touch(self):
        """Update last used time and increment use count"""
        self.last_used = time.time()
        self.use_count += 1

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if connection has expired"""
        return time.time() - self.last_used > ttl_seconds

    def age_seconds(self) -> float:
        """Get connection age in seconds"""
        return time.time() - self.created_at


class MCPConnectionPool:
    """
    Multi-user MCP connection pool with LRU eviction and TTL cleanup

    Features:
    - Per-user connection isolation
    - LRU eviction when max connections reached
    - TTL-based cleanup of inactive connections
    - Thread-safe async operations
    - Connection health monitoring
    """

    def __init__(
        self,
        max_connections: int = 100,  # 最大連線數
        ttl_seconds: int = 1800,  # 30分鐘 TTL
        cleanup_interval: int = 300,  # 5分鐘清理間隔
        enable_user_isolation: bool = True,
    ):
        self.max_connections = max_connections
        self.ttl_seconds = ttl_seconds
        self.cleanup_interval = cleanup_interval
        self.enable_user_isolation = enable_user_isolation

        # Connection storage - OrderedDict for LRU behavior
        self._connections: OrderedDict[str, ConnectionInfo] = OrderedDict()
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Metrics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cleanups": 0,
            "errors": 0,
        }

    def _generate_connection_key(
        self, mcp_config: Dict[str, Any], user_id: Optional[str] = None
    ) -> str:
        """Generate unique key for connection"""
        config_str = json.dumps(mcp_config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:16]

        if self.enable_user_isolation and user_id:
            return f"{user_id}:{config_hash}"
        return config_hash

    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for specific connection key"""
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def _create_connection(
        self, mcp_config: Dict[str, Any], user_id: Optional[str] = None
    ) -> MultiServerMCPClient:
        """Create new MCP client connection"""
        try:
            client = MultiServerMCPClient(mcp_config)
            await client.__aenter__()
            logger.info(f"Created new MCP connection for user {user_id}")
            return client
        except Exception as e:
            logger.error(f"Failed to create MCP connection: {e}")
            self._stats["errors"] += 1
            raise

    async def _evict_lru_connection(self):
        """Evict least recently used connection"""
        if not self._connections:
            return

        # Get the least recently used connection (first in OrderedDict)
        lru_key, connection_info = next(iter(self._connections.items()))

        try:
            await connection_info.client.__aexit__(None, None, None)
            logger.info(f"Evicted LRU connection: {lru_key}")
        except Exception as e:
            logger.warning(f"Error during LRU eviction: {e}")

        del self._connections[lru_key]
        if lru_key in self._locks:
            del self._locks[lru_key]

        self._stats["evictions"] += 1

    async def get_connection(
        self, mcp_config: Dict[str, Any], user_id: Optional[str] = None
    ) -> Optional[MultiServerMCPClient]:
        """Get or create MCP connection"""
        if not mcp_config:
            return None

        connection_key = self._generate_connection_key(mcp_config, user_id)
        lock = await self._get_lock(connection_key)

        async with lock:
            # Check if connection exists and is valid
            if connection_key in self._connections:
                connection_info = self._connections[connection_key]

                # Check if expired
                if connection_info.is_expired(self.ttl_seconds):
                    logger.info(f"Connection expired, removing: {connection_key}")
                    await self._remove_connection(connection_key)
                else:
                    # Move to end for LRU (most recently used)
                    self._connections.move_to_end(connection_key)
                    connection_info.touch()
                    self._stats["hits"] += 1
                    logger.debug(f"Reusing connection: {connection_key}")
                    return connection_info.client

            # Create new connection
            self._stats["misses"] += 1

            # Check if we need to evict connections first
            while len(self._connections) >= self.max_connections:
                await self._evict_lru_connection()

            # Create new connection
            try:
                client = await self._create_connection(mcp_config, user_id)

                # Store connection info
                config_hash = hashlib.sha256(
                    json.dumps(mcp_config, sort_keys=True).encode()
                ).hexdigest()[:16]

                connection_info = ConnectionInfo(
                    client=client,
                    created_at=time.time(),
                    last_used=time.time(),
                    user_id=user_id,
                    config_hash=config_hash,
                )
                connection_info.touch()

                self._connections[connection_key] = connection_info
                logger.info(f"Created new connection: {connection_key}")
                return client

            except Exception as e:
                logger.error(f"Failed to create connection {connection_key}: {e}")
                return None

    async def _remove_connection(self, connection_key: str):
        """Remove and cleanup a specific connection"""
        if connection_key in self._connections:
            connection_info = self._connections[connection_key]
            try:
                await connection_info.client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error cleaning up connection {connection_key}: {e}")

            del self._connections[connection_key]
            if connection_key in self._locks:
                del self._locks[connection_key]

    async def _cleanup_expired_connections(self):
        """Background task to cleanup expired connections"""
        expired_keys = []

        async with self._global_lock:
            current_time = time.time()
            for key, conn_info in self._connections.items():
                if conn_info.is_expired(self.ttl_seconds):
                    expired_keys.append(key)

        # Clean up expired connections
        for key in expired_keys:
            lock = await self._get_lock(key)
            async with lock:
                if key in self._connections:  # Double check
                    await self._remove_connection(key)
                    logger.info(f"Cleaned up expired connection: {key}")
                    self._stats["cleanups"] += 1

    async def start_background_cleanup(self):
        """Start background cleanup task"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._background_cleanup_loop())
            logger.info("Started MCP connection pool background cleanup")

    async def _background_cleanup_loop(self):
        """Background cleanup loop"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self.cleanup_interval
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                # Timeout is expected, run cleanup
                await self._cleanup_expired_connections()
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def shutdown(self):
        """Shutdown the connection pool"""
        logger.info("Shutting down MCP connection pool...")

        # Stop background cleanup
        self._shutdown_event.set()
        if self._cleanup_task:
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=10)
            except asyncio.TimeoutError:
                logger.warning("Background cleanup task did not shutdown gracefully")
                self._cleanup_task.cancel()

        # Close all connections
        connection_keys = list(self._connections.keys())
        for key in connection_keys:
            await self._remove_connection(key)

        logger.info("MCP connection pool shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            **self._stats,
            "active_connections": len(self._connections),
            "max_connections": self.max_connections,
            "ttl_seconds": self.ttl_seconds,
        }
    

    def get_connection_details(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all connections"""
        details = {}
        current_time = time.time()

        for key, conn_info in self._connections.items():
            details[key] = {
                "user_id": conn_info.user_id,
                "config_hash": conn_info.config_hash,
                "age_seconds": conn_info.age_seconds(),
                "last_used_seconds_ago": current_time - conn_info.last_used,
                "use_count": conn_info.use_count,
                "is_expired": conn_info.is_expired(self.ttl_seconds),
            }

        return details


# Global connection pool instance
_connection_pool: Optional[MCPConnectionPool] = None
_pool_lock = asyncio.Lock()


async def get_connection_pool() -> MCPConnectionPool:
    """Get global connection pool instance"""
    global _connection_pool

    if _connection_pool is None:
        async with _pool_lock:
            if _connection_pool is None:
                _connection_pool = MCPConnectionPool()
                await _connection_pool.start_background_cleanup()

    return _connection_pool


async def get_mcp_client(
    mcp_config: Dict[str, Any], user_id: Optional[str] = None
) -> Optional[MultiServerMCPClient]:
    """Get MCP client from connection pool"""
    if not mcp_config:
        return None

    pool = await get_connection_pool()
    return await pool.get_connection(mcp_config, user_id)


async def shutdown_connection_pool():
    """Shutdown global connection pool"""
    global _connection_pool

    if _connection_pool:
        await _connection_pool.shutdown()
        _connection_pool = None
