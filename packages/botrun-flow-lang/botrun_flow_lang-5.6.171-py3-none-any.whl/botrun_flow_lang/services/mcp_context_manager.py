"""
Simplified MCP context manager using connection pool
"""
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from .mcp_connection_pool import get_mcp_client


@asynccontextmanager
async def managed_mcp_client(
    mcp_config: Optional[Dict[str, Any]], 
    user_id: Optional[str] = None
):
    """
    Context manager for MCP client using connection pool
    
    Args:
        mcp_config: MCP configuration dict
        user_id: User ID for connection isolation
    
    Yields:
        MultiServerMCPClient or None if no config provided
    """
    if not mcp_config:
        yield None
        return
    
    client = await get_mcp_client(mcp_config, user_id)
    try:
        yield client
    except Exception as e:
        # Client errors are handled by the connection pool
        # No need to manually clean up - pool will handle it
        raise e
    # No explicit cleanup needed - connections are managed by the pool