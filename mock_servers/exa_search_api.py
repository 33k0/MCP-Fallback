# Exa Search MCP Server Mock
# Based on real Exa MCP server from exa-labs/exa-mcp-server
#
# Exa has 9 tools (3 enabled by default, 6 optional):
# DEFAULT ENABLED:
#   1. web_search_exa - General web search
#   2. get_code_context_exa - Find code examples from GitHub/SO/docs
#   3. company_research_exa - Research companies
# OPTIONAL (disabled by default):
#   4. web_search_advanced_exa - Advanced search with filters
#   5. deep_search_exa - Deep search with query expansion
#   6. crawling_exa - Get full content from a URL
#   7. people_search_exa - Find people's professional profiles
#   8. deep_researcher_start - Start AI research agent
#   9. deep_researcher_check - Check research task status
#
# For the benchmark, we'll include all 9 tools to test adaptation when
# falling back from Brave (2 tools) to Exa (9 tools).

from typing import Dict, Any, Optional, List
import uuid

DEFAULT_STATE = {
    "web_results": [
        {
            "title": "Python Official Documentation",
            "url": "https://docs.python.org",
            "text": "Welcome to Python.org. Python is a programming language that lets you work quickly and integrate systems more effectively.",
            "published_date": "2024-01-15",
            "author": "Python Software Foundation",
            "score": 0.95,
        },
        {
            "title": "Introduction to Machine Learning with Python",
            "url": "https://example.com/ml-python",
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn from data. Python provides excellent libraries like scikit-learn, TensorFlow, and PyTorch.",
            "published_date": "2024-01-10",
            "author": "AI Research Lab",
            "score": 0.89,
        },
        {
            "title": "Building REST APIs with FastAPI",
            "url": "https://fastapi.tiangolo.com",
            "text": "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.",
            "published_date": "2024-01-12",
            "author": "Sebastián Ramírez",
            "score": 0.87,
        },
    ],
    "code_results": [
        {
            "title": "How to read a file in Python - Stack Overflow",
            "url": "https://stackoverflow.com/questions/123456/read-file-python",
            "text": "with open('file.txt', 'r') as f:\n    content = f.read()\nprint(content)",
            "source": "stackoverflow",
            "language": "python",
            "score": 0.92,
        },
        {
            "title": "Python requests library usage - GitHub",
            "url": "https://github.com/psf/requests/blob/main/README.md",
            "text": "import requests\n\nresponse = requests.get('https://api.example.com/data')\ndata = response.json()",
            "source": "github",
            "language": "python",
            "score": 0.88,
        },
        {
            "title": "Async/await in Python - Official Docs",
            "url": "https://docs.python.org/3/library/asyncio.html",
            "text": "import asyncio\n\nasync def main():\n    await asyncio.sleep(1)\n    print('Hello')\n\nasyncio.run(main())",
            "source": "documentation",
            "language": "python",
            "score": 0.85,
        },
    ],
    "companies": [
        {
            "name": "OpenAI",
            "domain": "openai.com",
            "description": "OpenAI is an AI research and deployment company focused on ensuring artificial general intelligence benefits all of humanity.",
            "industry": "Artificial Intelligence",
            "founded": 2015,
            "headquarters": "San Francisco, CA",
            "employee_count": "500-1000",
            "funding": "$11.3B",
            "news": [
                {"title": "OpenAI Releases GPT-5", "date": "2024-01-20"},
                {"title": "OpenAI Partners with Microsoft", "date": "2024-01-15"},
            ],
        },
        {
            "name": "Anthropic",
            "domain": "anthropic.com",
            "description": "Anthropic is an AI safety company building reliable, interpretable, and steerable AI systems.",
            "industry": "Artificial Intelligence",
            "founded": 2021,
            "headquarters": "San Francisco, CA",
            "employee_count": "200-500",
            "funding": "$7.3B",
            "news": [
                {"title": "Anthropic Launches Claude 3", "date": "2024-01-18"},
                {"title": "Anthropic Raises Series C", "date": "2024-01-10"},
            ],
        },
    ],
    "people": [
        {
            "name": "Guido van Rossum",
            "title": "Creator of Python",
            "company": "Microsoft",
            "linkedin_url": "https://linkedin.com/in/guido-van-rossum",
            "twitter_handle": "@gaborvanrossum",
            "bio": "Guido van Rossum is a Dutch programmer best known as the creator of the Python programming language.",
        },
        {
            "name": "Yann LeCun",
            "title": "Chief AI Scientist",
            "company": "Meta",
            "linkedin_url": "https://linkedin.com/in/yann-lecun",
            "twitter_handle": "@ylecun",
            "bio": "Yann LeCun is a French computer scientist working in machine learning, computer vision, and neural networks.",
        },
    ],
    "research_tasks": {},
}


class ExaSearchAPI:
    """
    Mock Exa Search MCP Server.

    FEATURE-RICH TOOL SET (9 tools) - More capabilities than Brave (2 tools).

    Available tools:
    - web_search_exa: General web search with neural ranking
    - get_code_context_exa: Find code examples from GitHub/SO/docs
    - company_research_exa: Research companies for business info
    - web_search_advanced_exa: Advanced search with filters
    - deep_search_exa: Deep search with query expansion
    - crawling_exa: Get full content from a URL
    - people_search_exa: Find people's professional profiles
    - deep_researcher_start: Start AI research agent
    - deep_researcher_check: Check research task status

    This tests model adaptation when falling back FROM Brave (2 tools).
    The model needs to map simple search tasks to Exa's richer toolset.
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)

    # =========================================================================
    # Tool 1: web_search_exa (DEFAULT ENABLED)
    # =========================================================================

    def web_search_exa(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search the web using Exa's neural search.

        Performs a semantic search across the web and returns relevant results
        with clean, ready-to-use content. Uses neural ranking for better
        relevance than traditional keyword matching.

        Args:
            query (str): Natural language search query
            num_results (int): Number of results to return (max 100)

        Returns:
            dict: Search results with titles, URLs, text content, and relevance scores
        """
        query_lower = query.lower()
        matching_results = []

        for result in self.state["web_results"]:
            if (query_lower in result["title"].lower() or
                query_lower in result["text"].lower()):
                matching_results.append(result)

        if not matching_results:
            matching_results = self.state["web_results"]

        num_results = min(num_results, 100)
        paginated = matching_results[:num_results]

        return {
            "query": query,
            "total_results": len(matching_results),
            "results": [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "text": r["text"][:500],
                    "published_date": r.get("published_date"),
                    "author": r.get("author"),
                    "score": r.get("score", 0.5),
                }
                for r in paginated
            ],
        }

    # =========================================================================
    # Tool 2: get_code_context_exa (DEFAULT ENABLED)
    # =========================================================================

    def get_code_context_exa(
        self,
        query: str,
        language: str = None,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Find code examples, documentation, and programming solutions.

        Searches GitHub, Stack Overflow, and documentation sites to find
        relevant code examples and solutions. Optimized for programming queries.

        Args:
            query (str): Programming-related search query
            language (str): Optional programming language filter (e.g., "python", "javascript")
            num_results (int): Number of results to return

        Returns:
            dict: Code examples with source, language, and explanations
        """
        query_lower = query.lower()
        matching_results = []

        for result in self.state["code_results"]:
            if language and result.get("language", "").lower() != language.lower():
                continue
            if (query_lower in result["title"].lower() or
                query_lower in result["text"].lower()):
                matching_results.append(result)

        if not matching_results:
            matching_results = [r for r in self.state["code_results"]
                              if not language or r.get("language", "").lower() == language.lower()]

        if not matching_results:
            matching_results = self.state["code_results"]

        num_results = min(num_results, 50)
        paginated = matching_results[:num_results]

        return {
            "query": query,
            "language_filter": language,
            "total_results": len(matching_results),
            "results": [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "code": r["text"],
                    "source": r.get("source", "unknown"),
                    "language": r.get("language"),
                    "score": r.get("score", 0.5),
                }
                for r in paginated
            ],
        }

    # =========================================================================
    # Tool 3: company_research_exa (DEFAULT ENABLED)
    # =========================================================================

    def company_research_exa(
        self,
        company_name: str
    ) -> Dict[str, Any]:
        """
        Research a company to get business information, news, and insights.

        Returns comprehensive company data including description, industry,
        funding, employee count, and recent news. Useful for due diligence,
        competitive analysis, and business research.

        Args:
            company_name (str): Name of the company to research

        Returns:
            dict: Company profile with business details and recent news
        """
        name_lower = company_name.lower()

        for company in self.state["companies"]:
            if name_lower in company["name"].lower():
                return {
                    "found": True,
                    "company": {
                        "name": company["name"],
                        "domain": company["domain"],
                        "description": company["description"],
                        "industry": company["industry"],
                        "founded": company["founded"],
                        "headquarters": company["headquarters"],
                        "employee_count": company["employee_count"],
                        "funding": company["funding"],
                        "recent_news": company["news"],
                    },
                }

        return {
            "found": False,
            "company": None,
            "message": f"No company found matching '{company_name}'",
        }

    # =========================================================================
    # Tool 4: web_search_advanced_exa (OPTIONAL)
    # =========================================================================

    def web_search_advanced_exa(
        self,
        query: str,
        include_domains: List[str] = None,
        exclude_domains: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        num_results: int = 10,
        include_text: bool = True
    ) -> Dict[str, Any]:
        """
        Advanced web search with full control over filters.

        Provides fine-grained control over search results including domain
        filtering, date ranges, and content options. Use for precise searches.

        Args:
            query (str): Search query
            include_domains (List[str]): Only include results from these domains
            exclude_domains (List[str]): Exclude results from these domains
            start_date (str): Filter results after this date (YYYY-MM-DD)
            end_date (str): Filter results before this date (YYYY-MM-DD)
            num_results (int): Number of results to return
            include_text (bool): Whether to include full text content

        Returns:
            dict: Filtered search results with applied constraints
        """
        results = self.web_search_exa(query, num_results)

        # Apply domain filters (mock implementation)
        if include_domains:
            results["filters_applied"] = {"include_domains": include_domains}
        if exclude_domains:
            results["filters_applied"] = results.get("filters_applied", {})
            results["filters_applied"]["exclude_domains"] = exclude_domains
        if start_date or end_date:
            results["filters_applied"] = results.get("filters_applied", {})
            results["filters_applied"]["date_range"] = {"start": start_date, "end": end_date}

        results["advanced_search"] = True
        return results

    # =========================================================================
    # Tool 5: deep_search_exa (OPTIONAL)
    # =========================================================================

    def deep_search_exa(
        self,
        query: str,
        num_results: int = 20
    ) -> Dict[str, Any]:
        """
        Deep search with automatic query expansion for thorough research.

        Automatically expands the query to cover related topics and synonyms,
        providing more comprehensive results. Best for research tasks where
        you want broad coverage of a topic.

        Args:
            query (str): Initial search query
            num_results (int): Number of results to return

        Returns:
            dict: Expanded search results with related queries explored
        """
        # Simulate query expansion
        expanded_queries = [
            query,
            f"{query} tutorial",
            f"{query} examples",
            f"{query} best practices",
        ]

        base_results = self.web_search_exa(query, num_results)

        return {
            "original_query": query,
            "expanded_queries": expanded_queries,
            "total_results": base_results["total_results"],
            "results": base_results["results"],
            "deep_search": True,
        }

    # =========================================================================
    # Tool 6: crawling_exa (OPTIONAL)
    # =========================================================================

    def crawling_exa(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Get the full content of a specific webpage from a known URL.

        Fetches and extracts the main content from a URL, removing ads,
        navigation, and other clutter. Returns clean, readable text.

        Args:
            url (str): The URL to crawl and extract content from

        Returns:
            dict: Full page content with metadata
        """
        # Mock crawl response
        return {
            "url": url,
            "title": f"Content from {url}",
            "text": f"This is the extracted content from the webpage at {url}. In a real implementation, this would contain the full article text, cleaned and formatted for easy reading.",
            "word_count": 150,
            "published_date": "2024-01-15",
            "author": "Unknown",
            "crawled_at": "2024-01-20T12:00:00Z",
        }

    # =========================================================================
    # Tool 7: people_search_exa (OPTIONAL)
    # =========================================================================

    def people_search_exa(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Find people and their professional profiles.

        Searches for individuals and returns their professional information
        including current role, company, and social profiles.

        Args:
            query (str): Person name or description to search for
            num_results (int): Number of results to return

        Returns:
            dict: Professional profiles matching the query
        """
        query_lower = query.lower()
        matching_results = []

        for person in self.state["people"]:
            if (query_lower in person["name"].lower() or
                query_lower in person.get("bio", "").lower() or
                query_lower in person.get("company", "").lower()):
                matching_results.append(person)

        if not matching_results:
            matching_results = self.state["people"]

        num_results = min(num_results, 50)
        paginated = matching_results[:num_results]

        return {
            "query": query,
            "total_results": len(matching_results),
            "results": [
                {
                    "name": p["name"],
                    "title": p["title"],
                    "company": p["company"],
                    "linkedin_url": p.get("linkedin_url"),
                    "twitter_handle": p.get("twitter_handle"),
                    "bio": p.get("bio"),
                }
                for p in paginated
            ],
        }

    # =========================================================================
    # Tool 8: deep_researcher_start (OPTIONAL)
    # =========================================================================

    def deep_researcher_start(
        self,
        topic: str,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Start an AI research agent that searches, reads, and writes a report.

        Initiates an asynchronous deep research task that will explore the
        topic thoroughly and produce a detailed report. Use deep_researcher_check
        to monitor progress and retrieve results.

        Args:
            topic (str): The research topic or question
            depth (str): Research depth - 'quick', 'standard', or 'thorough'

        Returns:
            dict: Task ID and estimated completion time
        """
        task_id = str(uuid.uuid4())[:8]

        self.state["research_tasks"][task_id] = {
            "topic": topic,
            "depth": depth,
            "status": "in_progress",
            "progress": 0,
            "report": None,
        }

        return {
            "task_id": task_id,
            "topic": topic,
            "depth": depth,
            "status": "started",
            "estimated_time": "2-5 minutes" if depth == "standard" else "5-10 minutes",
            "message": f"Research task started. Use deep_researcher_check with task_id '{task_id}' to check status.",
        }

    # =========================================================================
    # Tool 9: deep_researcher_check (OPTIONAL)
    # =========================================================================

    def deep_researcher_check(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Check status and get results from a deep research task.

        Retrieves the current status of a research task started with
        deep_researcher_start. Returns progress percentage and the
        final report when complete.

        Args:
            task_id (str): The task ID returned by deep_researcher_start

        Returns:
            dict: Task status, progress, and report (if complete)
        """
        if task_id not in self.state["research_tasks"]:
            return {
                "error": f"Task '{task_id}' not found",
                "found": False,
            }

        task = self.state["research_tasks"][task_id]

        # Simulate progress (in real mock, would track actual time)
        task["progress"] = min(task["progress"] + 50, 100)
        if task["progress"] >= 100:
            task["status"] = "completed"
            task["report"] = f"""
# Research Report: {task['topic']}

## Executive Summary
This report provides a comprehensive analysis of {task['topic']}.

## Key Findings
1. Finding one related to the topic
2. Finding two with supporting evidence
3. Finding three with implications

## Detailed Analysis
Lorem ipsum dolor sit amet, consectetur adipiscing elit. The research
uncovered several important insights about {task['topic']}.

## Conclusion
Based on the research, we recommend further investigation into specific
aspects of {task['topic']}.
"""

        return {
            "task_id": task_id,
            "topic": task["topic"],
            "status": task["status"],
            "progress": task["progress"],
            "report": task["report"] if task["status"] == "completed" else None,
        }
