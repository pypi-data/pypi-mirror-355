# MCP Conceptual

An MCP (Model Context Protocol) server for the Conceptual Keywords & Creative Performance API. This server provides access to keyword and creative performance data from Google Ads and Meta advertising platforms.

## Features

- **Keywords Performance**: Get keyword metrics, CAC analysis, and performance data
- **Search Terms**: Retrieve search terms that triggered your ads
- **Creative Performance**: Access Meta and Google Ads creative performance data
- **Creative Management**: Get and update creative status (pause/activate)
- **Account Metrics**: Get account-level performance metrics by campaign type (Google Ads)
- **Campaign Metrics**: Get campaign-level performance metrics for Google Ads and Meta
- **Budget Efficiency**: Get automated budget and efficiency checks
- **Rate Limiting**: Built-in awareness of API rate limits
- **Error Handling**: Comprehensive error handling with helpful messages

## Installation

### Using uvx (Recommended)

```bash
uvx mcp-conceptual
```

### From Source

```bash
git clone <repository-url>
cd mcp-conceptual
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Required
CONCEPTUAL_API_KEY=your_api_key_here

# Optional (defaults to production)
CONCEPTUAL_BASE_URL=https://api.conceptual.com/api
```

### Getting an API Key

1. Log into your Conceptual account
2. Go to Account Settings
3. Generate an API key for your customer account
4. Set the `CONCEPTUAL_API_KEY` environment variable

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "conceptual": {
      "command": "uvx",
      "args": ["mcp-conceptual"],
      "env": {
        "CONCEPTUAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Standalone

```bash
# Run the server
mcp-conceptual

# Or with uvx
uvx mcp-conceptual
```

## Available Tools

### Keywords Tools

#### `get_keyword_performance`
Get keyword performance data including cost, clicks, conversions, and CAC analysis.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `view_type`: keywords, search_terms, manual, or campaign_content (default: keywords)
- `advanced_mode`: Include advanced metrics (default: false)
- `limit`: Max records to return (1-1000, default: 100)
- `offset`: Records to skip for pagination (default: 0)
- `sort_by`: Field to sort by (cost, clicks, impressions, conversions, cac, ctr, cpc, conversion_rate)
- `sort_direction`: asc or desc (default: desc)

**Rate limit:** 60 requests per minute

#### `get_search_terms_performance`
Get search terms that triggered your ads with performance metrics.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `advanced_mode`: Include advanced metrics (default: false)
- `limit`: Max records to return (1-1000, default: 100)
- `offset`: Records to skip for pagination (default: 0)
- `sort_by`: Field to sort by
- `sort_direction`: asc or desc (default: desc)

**Rate limit:** 60 requests per minute  
**Note:** May be slower due to large volume of search terms data

#### `get_manual_keywords_info`
Get information about manual keywords functionality.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

#### `get_campaign_content_info`
Get information about campaign content functionality.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

### Creative Tools

#### `get_meta_creative_performance`
Get Meta (Facebook/Instagram) creative performance data.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `platform`: meta, google, or all (default: all)
- `status`: active, paused, or all (default: all)
- `limit`: Max records to return (1-500, default: 100)
- `offset`: Records to skip for pagination (default: 0)
- `include_images`: Include creative image URLs (default: true)
- `sort_by`: Field to sort by (spend, impressions, clicks, conversions, cpm, cpc, ctr, conversion_rate)
- `sort_direction`: asc or desc (default: desc)

**Rate limit:** 30 requests per minute

#### `get_google_creative_performance`
Get Google Ads creative performance data.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `limit`: Max records to return (1-500, default: 100)
- `offset`: Records to skip for pagination (default: 0)
- `sort_by`: Field to sort by
- `sort_direction`: asc or desc (default: desc)

**Rate limit:** 30 requests per minute

#### `get_creative_status`
Get the current status of a specific creative/ad.

**Parameters:**
- `creative_id` (required): Creative/Ad ID

#### `update_creative_status`
Update the status of a creative/ad (pause or activate).

**Parameters:**
- `creative_id` (required): Creative/Ad ID
- `status` (required): New status (ACTIVE, PAUSED, active, or paused)

**Rate limit:** 10 requests per minute  
**Note:** Requires Meta OAuth permissions for the customer account

### Metrics Tools

#### `get_account_metrics`
Get account-level performance metrics by campaign type (Google Ads only).

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `advanced_mode`: Include advanced metrics and analysis (default: false)

**Rate limit:** 60 requests per minute

#### `get_campaign_metrics`
Get campaign-level performance metrics for Google Ads and/or Meta platforms.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `platform`: google, meta, or all (default: all)
- `advanced_mode`: Include advanced metrics and analysis (default: false)
- `limit`: Max records to return (1-1000, default: 100)
- `offset`: Records to skip for pagination (default: 0)
- `sort_by`: Field to sort by (cost, campaign_name, conversions, cac, roas)
- `sort_direction`: asc or desc (default: desc)

**Rate limit:** 60 requests per minute

#### `get_budget_efficiency_metrics`
Get automated budget and efficiency checks.

**Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Rate limit:** 60 requests per minute

## Rate Limits

- Keywords endpoints: 60 requests per minute
- Creative endpoints: 30 requests per minute
- Creative status updates: 10 requests per minute
- Metrics endpoints: 60 requests per minute

## Data Caching

Data is cached for 120 minutes to ensure optimal performance. Cache expiration times are included in response metadata.

## Error Handling

The server handles various error conditions:

- **401 Unauthorized**: Invalid or missing API key
- **400 Bad Request**: Missing platform configuration or invalid parameters
- **422 Validation Error**: Invalid date formats or parameter values
- **429 Rate Limit**: Rate limit exceeded (includes retry suggestions)
- **500 Server Error**: Internal API errors
- **504 Timeout**: Query timeout (for search terms with large datasets)

## Development

### Setup

```bash
git clone <repository-url>
cd mcp-conceptual
pip install -e ".[dev]"
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

### Testing

```bash
pytest
```

## License

MIT License - see LICENSE file for details.

## Support

For API support, contact: support@conceptualhq.com

For issues with this MCP server, please file an issue in the repository.