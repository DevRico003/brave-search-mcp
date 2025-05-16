from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os

from utils import get_brave_client, BraveSearchClient

load_dotenv()

# Create a dataclass for our application context
@dataclass
class BraveSearchContext:
    """Context for the Brave Search MCP server."""
    brave_client: BraveSearchClient

@asynccontextmanager
async def brave_search_lifespan(server: FastMCP) -> AsyncIterator[BraveSearchContext]:
    """
    Manages the Brave Search client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        BraveSearchContext: The context containing the Brave Search client
    """
    # Create and return the Brave Search client
    brave_client = get_brave_client()
    
    try:
        yield BraveSearchContext(brave_client=brave_client)
    finally:
        # Close the HTTP client when shutting down
        await brave_client.close()

# Initialize FastMCP server with the Brave Search client as context
mcp = FastMCP(
    "mcp-brave-search",
    description="MCP server for Brave Search API integration",
    lifespan=brave_search_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8053")
)        

@mcp.tool()
async def brave_web_search(ctx: Context, query: str, count: int = 10, offset: int = 0) -> str:
    """Performs a web search using the Brave Search API.
    
    Ideal for general queries, news, articles, and online content.
    Use this for broad information gathering, recent events, or when you need diverse web sources.
    
    Args:
        ctx: The MCP server provided context which includes the Brave Search client
        query: Search query (max 400 chars, 50 words)
        count: Number of results (1-20, default 10)
        offset: Pagination offset (max 9, default 0)
    """
    try:
        brave_client = ctx.request_context.lifespan_context.brave_client
        results = await brave_client.web_search(query, count, offset)
        return results
    except Exception as e:
        return f"Error during web search: {str(e)}"

@mcp.tool()
async def brave_local_search(ctx: Context, query: str, count: int = 5) -> str:
    """Searches for local businesses and places using Brave's Local Search API.
    
    Best for queries related to physical locations, businesses, restaurants, services, etc.
    Returns detailed information including business names, addresses, ratings, phone numbers and opening hours.
    
    Args:
        ctx: The MCP server provided context which includes the Brave Search client
        query: Local search query (e.g. 'pizza near Central Park')
        count: Number of results (1-20, default 5)
    """
    try:
        brave_client = ctx.request_context.lifespan_context.brave_client
        results = await brave_client.local_search(query, count)
        return results
    except Exception as e:
        return f"Error during local search: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())