# Brave Search MCP Server Mock
# Based on real Brave Search MCP server from modelcontextprotocol/servers
#
# Brave Search has only 2 tools:
#   1. brave_web_search - General web search
#   2. brave_local_search - Local business/place search
#
# This is a minimal search API - good for testing fallback to more feature-rich
# alternatives like Exa (which has 9 tools).

from typing import Dict, Any, Optional, List

DEFAULT_STATE = {
    "web_results": [
        {
            "title": "Python Official Documentation",
            "url": "https://docs.python.org",
            "description": "Welcome to Python.org, the official home of the Python programming language.",
            "age": "2 days ago",
        },
        {
            "title": "Learn Python - Free Interactive Tutorial",
            "url": "https://www.learnpython.org",
            "description": "Learn Python the easy way with interactive tutorials and exercises.",
            "age": "1 week ago",
        },
        {
            "title": "Real Python Tutorials",
            "url": "https://realpython.com",
            "description": "Learn Python programming with tutorials, guides, and articles for all skill levels.",
            "age": "3 days ago",
        },
        {
            "title": "QuantumLeaf Framework - Official Docs",
            "url": "https://quantumleaf.dev/docs",
            "description": "QuantumLeaf is a reactive state management framework for distributed edge computing. Getting started guide and API reference.",
            "age": "4 days ago",
        },
        {
            "title": "QuantumLeaf vs Riverpod: A Comparison",
            "url": "https://blog.devcraft.io/quantumleaf-comparison",
            "description": "An in-depth comparison of QuantumLeaf's reactive state propagation model with traditional state management approaches.",
            "age": "1 week ago",
        },
        {
            "title": "Building microservices with QuantumLeaf 3.0",
            "url": "https://medium.com/@techdev/quantumleaf-microservices",
            "description": "Tutorial: How to use QuantumLeaf 3.0 for building fault-tolerant microservices with automatic state reconciliation.",
            "age": "2 days ago",
        },
        {
            "title": "Velox Dynamics - Company Profile",
            "url": "https://veloxdynamics.com/about",
            "description": "Velox Dynamics is a Series B startup building next-generation autonomous logistics infrastructure. Founded 2023 in Palo Alto.",
            "age": "6 days ago",
        },
        {
            "title": "Velox Dynamics Raises $47M Series B",
            "url": "https://techcrunch.fake/velox-series-b",
            "description": "Velox Dynamics announced a $47M Series B round led by Andreessen Horowitz to expand its autonomous freight routing platform.",
            "age": "3 days ago",
        },
    ],
    "local_results": [
        {
            "name": "The Coffee House",
            "address": "123 Main Street, San Francisco, CA 94102",
            "phone": "(415) 555-0123",
            "rating": 4.5,
            "reviews": 234,
            "category": "Coffee Shop",
            "hours": "Mon-Fri 6am-8pm, Sat-Sun 7am-6pm",
            "price_range": "$$",
        },
        {
            "name": "Bay Area Bikes",
            "address": "456 Market Street, San Francisco, CA 94103",
            "phone": "(415) 555-0456",
            "rating": 4.8,
            "reviews": 89,
            "category": "Bicycle Shop",
            "hours": "Mon-Sat 9am-7pm, Sun 10am-5pm",
            "price_range": "$$$",
        },
        {
            "name": "Golden Gate Diner",
            "address": "789 Mission Street, San Francisco, CA 94105",
            "phone": "(415) 555-0789",
            "rating": 4.2,
            "reviews": 567,
            "category": "American Restaurant",
            "hours": "Daily 7am-10pm",
            "price_range": "$$",
        },
    ],
}


class BraveSearchAPI:
    """
    Mock Brave Search MCP Server.

    MINIMAL TOOL SET (2 tools) - This is a simple search API.

    Available tools:
    - brave_web_search: Search the web for any topic
    - brave_local_search: Search for local businesses and places

    Compared to Exa (9 tools), Brave lacks:
    - Code-specific search
    - Company research
    - People search
    - Deep research/crawling capabilities
    - Advanced filtering options
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)
        self.state["_search_epoch"] = 0

    def invalidate_transient_handles(self) -> None:
        """Advance epoch to make previous result identifiers stale."""
        self.state["_search_epoch"] += 1

    # =========================================================================
    # Tool 1: brave_web_search
    # =========================================================================

    def brave_web_search(
        self,
        query: str,
        count: int = 10,
        offset: int = 0,
        freshness: str = None,
        safe_search: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Search the web using Brave Search.

        Performs a general web search and returns relevant results with titles,
        URLs, descriptions, and publication dates.

        Args:
            query (str): The search query string
            count (int): Number of results to return (max 20)
            offset (int): Pagination offset (max 9)
            freshness (str): Filter by time - 'day', 'week', 'month', or None for all
            safe_search (str): Safe search level - 'off', 'moderate', 'strict'

        Returns:
            dict: Search results with web pages matching the query
        """
        self.state["_search_epoch"] += 1
        # Filter results based on query (simple keyword matching for mock)
        query_lower = query.lower()
        matching_results = []

        for result in self.state["web_results"]:
            if (query_lower in result["title"].lower() or
                query_lower in result["description"].lower()):
                matching_results.append(result)

        # If no matches, return all results (simulating broad search)
        if not matching_results:
            matching_results = self.state["web_results"]

        # Apply pagination
        count = min(count, 20)
        offset = min(offset, 9)
        paginated = matching_results[offset:offset + count]

        return {
            "query": query,
            "search_epoch": self.state["_search_epoch"],
            "total_results": len(matching_results),
            "results": [
                {
                    "result_id": f"brv_{self.state['_search_epoch']}_{i}",
                    "title": r["title"],
                    "url": r["url"],
                    "description": r["description"],
                    "age": r.get("age", "Unknown"),
                }
                for i, r in enumerate(paginated)
            ],
            "freshness": freshness,
            "safe_search": safe_search,
        }

    # =========================================================================
    # Tool 2: brave_local_search
    # =========================================================================

    def brave_local_search(
        self,
        query: str,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Search for local businesses and places using Brave Search.

        Returns detailed information about local businesses including ratings,
        hours, contact info, and reviews. Useful for finding restaurants,
        shops, services, and other local establishments.

        Note: Requires Brave Search Pro plan for full capabilities.
        Falls back to web search on free tier.

        Args:
            query (str): Search query for local businesses (e.g., "coffee shops near me")
            count (int): Number of results to return (max 20)

        Returns:
            dict: Local business results with detailed information
        """
        self.state["_search_epoch"] += 1
        query_lower = query.lower()
        matching_results = []

        for result in self.state["local_results"]:
            if (query_lower in result["name"].lower() or
                query_lower in result["category"].lower() or
                query_lower in result["address"].lower()):
                matching_results.append(result)

        # If no matches, return all results
        if not matching_results:
            matching_results = self.state["local_results"]

        count = min(count, 20)
        paginated = matching_results[:count]

        return {
            "query": query,
            "search_epoch": self.state["_search_epoch"],
            "total_results": len(matching_results),
            "results": [
                {
                    "result_id": f"brv_local_{self.state['_search_epoch']}_{i}",
                    "name": r["name"],
                    "address": r["address"],
                    "phone": r["phone"],
                    "rating": r["rating"],
                    "reviews": r["reviews"],
                    "category": r["category"],
                    "hours": r["hours"],
                    "price_range": r.get("price_range", "Unknown"),
                }
                for i, r in enumerate(paginated)
            ],
        }
