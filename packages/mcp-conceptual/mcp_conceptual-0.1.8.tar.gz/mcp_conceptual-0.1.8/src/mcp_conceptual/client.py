"""API client for Conceptual Keywords & Creative Performance API."""

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .models import (
    CampaignContentResponse,
    CreativeResponse,
    CreativeStatusResponse,
    CreativeStatusUpdateResponse,
    ErrorResponse,
    KeywordResponse,
    ManualKeywordsResponse,
)


class ConceptualAPIError(Exception):
    """Base exception for Conceptual API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_type: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(message)


class ConceptualAPIClient:
    """Client for the Conceptual Keywords & Creative Performance API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("CONCEPTUAL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set CONCEPTUAL_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or os.getenv("CONCEPTUAL_BASE_URL", "https://api.conceptualhq.com/api")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an API endpoint."""
        base = self.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base}/{endpoint}"
    
    def _add_api_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add API key to request parameters."""
        params = params.copy()
        params["api_key"] = self.api_key
        return params
    
    async def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request and handle errors."""
        url = self._build_url(endpoint)
        params = self._add_api_key(params or {})
        
        try:
            response = await self.client.request(method, url, params=params, json=json)
            response_data = response.json()
            
            if response.status_code >= 400:
                error_msg = response_data.get("message", f"HTTP {response.status_code}")
                error_type = response_data.get("error", "Unknown Error")
                raise ConceptualAPIError(error_msg, response.status_code, error_type)
            
            return response_data
            
        except httpx.RequestError as e:
            raise ConceptualAPIError(f"Request failed: {e}")
        except (KeyError, ValueError) as e:
            raise ConceptualAPIError(f"Invalid response format: {e}")
    
    async def get_keyword_performance(
        self,
        start_date: str,
        end_date: str,
        view_type: str = "keywords",
        advanced_mode: bool = False,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> KeywordResponse:
        """Get keyword performance data."""
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "view_type": view_type,
            "advanced_mode": advanced_mode,
            "limit": limit,
            "offset": offset,
            "sort_direction": sort_direction,
        }
        if sort_by:
            params["sort_by"] = sort_by
        
        data = await self._make_request("GET", "/keywords/performance", params)
        return KeywordResponse(**data)
    
    async def get_search_terms_performance(
        self,
        start_date: str,
        end_date: str,
        advanced_mode: bool = False,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> KeywordResponse:
        """Get search terms performance data."""
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "advanced_mode": advanced_mode,
            "limit": limit,
            "offset": offset,
            "sort_direction": sort_direction,
        }
        if sort_by:
            params["sort_by"] = sort_by
        
        data = await self._make_request("GET", "/keywords/search-terms", params)
        return KeywordResponse(**data)
    
    async def get_manual_keywords_info(
        self, start_date: str, end_date: str
    ) -> ManualKeywordsResponse:
        """Get manual keywords information."""
        params = {"start_date": start_date, "end_date": end_date}
        data = await self._make_request("GET", "/keywords/manual", params)
        return ManualKeywordsResponse(**data)
    
    async def get_campaign_content_info(
        self, start_date: str, end_date: str
    ) -> CampaignContentResponse:
        """Get campaign content information."""
        params = {"start_date": start_date, "end_date": end_date}
        data = await self._make_request("GET", "/keywords/campaign-content", params)
        return CampaignContentResponse(**data)
    
    async def get_meta_creative_performance(
        self,
        start_date: str,
        end_date: str,
        platform: str = "all",
        status: str = "all",
        limit: int = 100,
        offset: int = 0,
        include_images: bool = True,
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> CreativeResponse:
        """Get Meta creative performance data."""
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "platform": platform,
            "status": status,
            "limit": min(limit, 500),  # API max is 500 for creatives
            "offset": offset,
            "include_images": include_images,
            "sort_direction": sort_direction,
        }
        if sort_by:
            params["sort_by"] = sort_by
        
        data = await self._make_request("GET", "/creatives/meta", params)
        return CreativeResponse(**data)
    
    async def get_google_creative_performance(
        self,
        start_date: str,
        end_date: str,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> CreativeResponse:
        """Get Google Ads creative performance data."""
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "limit": min(limit, 500),  # API max is 500 for creatives
            "offset": offset,
            "sort_direction": sort_direction,
        }
        if sort_by:
            params["sort_by"] = sort_by
        
        data = await self._make_request("GET", "/creatives/google", params)
        return CreativeResponse(**data)
    
    async def get_creative_status(self, creative_id: str) -> CreativeStatusResponse:
        """Get creative status."""
        data = await self._make_request("GET", f"/creatives/{creative_id}/status")
        return CreativeStatusResponse(**data)
    
    async def update_creative_status(
        self, creative_id: str, status: str
    ) -> CreativeStatusUpdateResponse:
        """Update creative status."""
        json_data = {"status": status}
        data = await self._make_request("PUT", f"/creatives/{creative_id}/status", json=json_data)
        return CreativeStatusUpdateResponse(**data)