"""MCP Server for Conceptual Keywords & Creative Performance API."""

import os
import sys
from typing import Sequence

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .tools.creatives import (
    get_creative_status,
    get_google_creative_performance,
    get_meta_creative_performance,
    update_creative_status,
)
from .tools.keywords import (
    get_campaign_content_info,
    get_keyword_performance,
    get_manual_keywords_info,
    get_search_terms_performance,
)

# Load environment variables
load_dotenv()

# Check for required environment variables
api_key = os.getenv("CONCEPTUAL_API_KEY")
if not api_key:
    print("Error: CONCEPTUAL_API_KEY environment variable is required", file=sys.stderr)
    print("Please set your API key in the environment or .env file", file=sys.stderr)
    sys.exit(1)

# Create server instance
mcp = FastMCP("Conceptual API Server")


@mcp.tool()
async def get_keyword_performance_tool(
    start_date: str,
    end_date: str,
    view_type: str = "keywords",
    advanced_mode: bool = False,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = None,
    sort_direction: str = "desc",
) -> str:
    """Get keyword performance data including cost, clicks, conversions, and CAC analysis.
    
    Rate limit: 60 requests per minute
    Data is cached for 120 minutes
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD) 
        view_type: keywords, search_terms, manual, or campaign_content (default: keywords)
        advanced_mode: Include advanced metrics (default: false)
        limit: Max records to return (1-1000, default: 100)
        offset: Records to skip for pagination (default: 0)
        sort_by: Field to sort by (cost, clicks, impressions, conversions, cac, ctr, cpc, conversion_rate)
        sort_direction: asc or desc (default: desc)
    """
    result = await get_keyword_performance(
        start_date, end_date, view_type, advanced_mode, limit, offset, sort_by, sort_direction
    )
    return result[0].text


@mcp.tool()
async def get_search_terms_performance_tool(
    start_date: str,
    end_date: str,
    advanced_mode: bool = False,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = None,
    sort_direction: str = "desc",
) -> str:
    """Get search terms that triggered your ads with performance metrics.
    
    Rate limit: 60 requests per minute
    Note: May be slower due to large volume of search terms data
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        advanced_mode: Include advanced metrics (default: false)
        limit: Max records to return (1-1000, default: 100)
        offset: Records to skip for pagination (default: 0)
        sort_by: Field to sort by (cost, clicks, impressions, conversions, cac, ctr, cpc, conversion_rate)
        sort_direction: asc or desc (default: desc)
    """
    result = await get_search_terms_performance(
        start_date, end_date, advanced_mode, limit, offset, sort_by, sort_direction
    )
    return result[0].text


@mcp.tool()
async def get_manual_keywords_info_tool(start_date: str, end_date: str) -> str:
    """Get information about manual keywords functionality.
    
    Manual keywords are used for campaign generation, not performance analysis.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    result = await get_manual_keywords_info(start_date, end_date)
    return result[0].text


@mcp.tool()
async def get_campaign_content_info_tool(start_date: str, end_date: str) -> str:
    """Get information about campaign content functionality.
    
    Campaign content is used for managing campaign templates and content.
    
    Args:
        start_date: Start date (YYYY-MM-DD)  
        end_date: End date (YYYY-MM-DD)
    """
    result = await get_campaign_content_info(start_date, end_date)
    return result[0].text


@mcp.tool()
async def get_meta_creative_performance_tool(
    start_date: str,
    end_date: str,
    platform: str = "all",
    status: str = "all",
    limit: int = 100,
    offset: int = 0,
    include_images: bool = True,
    sort_by: str = None,
    sort_direction: str = "desc",
) -> str:
    """Get Meta (Facebook/Instagram) creative performance data.
    
    Rate limit: 30 requests per minute
    Includes creative assets, performance metrics, and optimization insights.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        platform: meta, google, or all (default: all)
        status: active, paused, or all (default: all)
        limit: Max records to return (1-500, default: 100)
        offset: Records to skip for pagination (default: 0)
        include_images: Include creative image URLs (default: true)
        sort_by: Field to sort by (spend, impressions, clicks, conversions, cpm, cpc, ctr, conversion_rate)
        sort_direction: asc or desc (default: desc)
    """
    result = await get_meta_creative_performance(
        start_date, end_date, platform, status, limit, offset, include_images, sort_by, sort_direction
    )
    return result[0].text


@mcp.tool()
async def get_google_creative_performance_tool(
    start_date: str,
    end_date: str,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = None,
    sort_direction: str = "desc",
) -> str:
    """Get Google Ads creative performance data.
    
    Rate limit: 30 requests per minute
    Includes asset-level performance metrics and optimization insights.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max records to return (1-500, default: 100)
        offset: Records to skip for pagination (default: 0)
        sort_by: Field to sort by (spend, impressions, clicks, conversions, cpm, cpc, ctr, conversion_rate)
        sort_direction: asc or desc (default: desc)
    """
    result = await get_google_creative_performance(
        start_date, end_date, limit, offset, sort_by, sort_direction
    )
    return result[0].text


@mcp.tool()
async def get_creative_status_tool(creative_id: str) -> str:
    """Get the current status of a specific creative/ad.
    
    Args:
        creative_id: Creative/Ad ID to check status for
    """
    result = await get_creative_status(creative_id)
    return result[0].text


@mcp.tool()
async def update_creative_status_tool(creative_id: str, status: str) -> str:
    """Update the status of a creative/ad (pause or activate).
    
    Rate limit: 10 requests per minute
    Requires Meta OAuth permissions for the customer account.
    
    Args:
        creative_id: Creative/Ad ID to update
        status: New status (ACTIVE, PAUSED, active, or paused - case insensitive)
    """
    result = await update_creative_status(creative_id, status)
    return result[0].text


def cli_main():
    """CLI entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    cli_main()