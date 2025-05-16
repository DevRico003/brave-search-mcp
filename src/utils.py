import os
import httpx
from typing import Dict, List, Any, Optional

# Rate limit configuration
RATE_LIMIT = {
    "per_second": 1,
    "per_month": 15000
}

# Request counter
request_count = {
    "second": 0,
    "month": 0,
    "last_reset": 0
}

def check_rate_limit():
    """
    Check if we're within rate limits for the Brave API.
    
    Raises:
        Exception: If rate limit is exceeded
    """
    import time
    
    now = int(time.time() * 1000)
    if now - request_count["last_reset"] > 1000:
        request_count["second"] = 0
        request_count["last_reset"] = now
        
    if (request_count["second"] >= RATE_LIMIT["per_second"] or
        request_count["month"] >= RATE_LIMIT["per_month"]):
        raise Exception("Rate limit exceeded")
        
    request_count["second"] += 1
    request_count["month"] += 1

class BraveSearchClient:
    """Client for the Brave Search API."""
    
    def __init__(self):
        """Initialize the Brave Search client."""
        self.api_key = os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY environment variable is required")
            
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key
            }
        )
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        
    async def web_search(self, query: str, count: int = 10, offset: int = 0) -> str:
        """
        Perform a web search using the Brave Search API.
        
        Args:
            query: Search query (max 400 chars, 50 words)
            count: Number of results (1-20, default 10)
            offset: Pagination offset (max 9, default 0)
            
        Returns:
            Formatted string of search results
        """
        check_rate_limit()
        
        # API limit for count
        count = min(count, 20)
        
        params = {
            "q": query,
            "count": str(count),
            "offset": str(offset)
        }
        
        response = await self.client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Brave API error: {response.status_code} {response.text}")
            
        data = response.json()
        
        # Extract web results
        results = []
        if "web" in data and "results" in data["web"]:
            for result in data["web"]["results"]:
                results.append({
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "url": result.get("url", "")
                })
                
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append(
                f"Title: {r['title']}\nDescription: {r['description']}\nURL: {r['url']}"
            )
            
        return "\n\n".join(formatted_results)
        
    async def local_search(self, query: str, count: int = 5) -> str:
        """
        Search for local businesses and places using Brave's Local Search API.
        
        Args:
            query: Local search query (e.g. 'pizza near Central Park')
            count: Number of results (1-20, default 5)
            
        Returns:
            Formatted string of local search results or web search results if none found
        """
        check_rate_limit()
        
        # Initial search to get location IDs
        params = {
            "q": query,
            "search_lang": "en",
            "result_filter": "locations",
            "count": str(min(count, 20))
        }
        
        response = await self.client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Brave API error: {response.status_code} {response.text}")
            
        data = response.json()
        
        # Extract location IDs
        location_ids = []
        if "locations" in data and "results" in data["locations"]:
            for location in data["locations"]["results"]:
                if "id" in location:
                    location_ids.append(location["id"])
                    
        # If no location IDs found, fall back to web search
        if not location_ids:
            return await self.web_search(query, count)
            
        # Get POI details and descriptions
        pois_data = await self._get_pois_data(location_ids)
        descriptions_data = await self._get_descriptions_data(location_ids)
        
        return self._format_local_results(pois_data, descriptions_data)
        
    async def _get_pois_data(self, ids: List[str]) -> Dict[str, Any]:
        """
        Get point of interest data for location IDs.
        
        Args:
            ids: List of location IDs
            
        Returns:
            Dictionary of POI data
        """
        check_rate_limit()
        
        params = {}
        for id in ids:
            if id:  # Ensure ID is not empty
                params.setdefault("ids", []).append(id)
                
        response = await self.client.get(
            "https://api.search.brave.com/res/v1/local/pois",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Brave API error: {response.status_code} {response.text}")
            
        return response.json()
        
    async def _get_descriptions_data(self, ids: List[str]) -> Dict[str, Any]:
        """
        Get descriptions for location IDs.
        
        Args:
            ids: List of location IDs
            
        Returns:
            Dictionary of descriptions data
        """
        check_rate_limit()
        
        params = {}
        for id in ids:
            if id:  # Ensure ID is not empty
                params.setdefault("ids", []).append(id)
                
        response = await self.client.get(
            "https://api.search.brave.com/res/v1/local/descriptions",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Brave API error: {response.status_code} {response.text}")
            
        return response.json()
        
    def _format_local_results(self, pois_data: Dict[str, Any], desc_data: Dict[str, Any]) -> str:
        """
        Format local search results.
        
        Args:
            pois_data: POI data from the API
            desc_data: Description data from the API
            
        Returns:
            Formatted string of local search results
        """
        formatted_results = []
        
        if "results" in pois_data:
            for poi in pois_data["results"]:
                # Format address
                address_parts = []
                if "address" in poi:
                    if poi["address"].get("streetAddress"):
                        address_parts.append(poi["address"]["streetAddress"])
                    if poi["address"].get("addressLocality"):
                        address_parts.append(poi["address"]["addressLocality"])
                    if poi["address"].get("addressRegion"):
                        address_parts.append(poi["address"]["addressRegion"])
                    if poi["address"].get("postalCode"):
                        address_parts.append(poi["address"]["postalCode"])
                
                address = ", ".join(address_parts) if address_parts else "N/A"
                
                # Get rating information
                rating_value = "N/A"
                rating_count = 0
                if "rating" in poi:
                    rating_value = poi["rating"].get("ratingValue", "N/A")
                    rating_count = poi["rating"].get("ratingCount", 0)
                
                # Get opening hours
                hours = "N/A"
                if "openingHours" in poi and poi["openingHours"]:
                    hours = ", ".join(poi["openingHours"])
                
                # Get description
                description = "No description available"
                if "descriptions" in desc_data and poi["id"] in desc_data["descriptions"]:
                    description = desc_data["descriptions"][poi["id"]]
                
                # Format result
                result = f"""Name: {poi.get('name', 'Unknown')}
Address: {address}
Phone: {poi.get('phone', 'N/A')}
Rating: {rating_value} ({rating_count} reviews)
Price Range: {poi.get('priceRange', 'N/A')}
Hours: {hours}
Description: {description}
"""
                formatted_results.append(result)
                
        if not formatted_results:
            return "No local results found"
            
        return "\n---\n".join(formatted_results)

def get_brave_client():
    """
    Initialize and return a Brave Search client.
    
    Returns:
        BraveSearchClient: The initialized client
    """
    return BraveSearchClient()