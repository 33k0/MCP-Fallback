# MCP Registry System
# Models must first discover available MCPs, then mount one to see its tools
# This simulates real-world tool discovery and prevents seeing all options at once

# Server names are explicit brand names for easier identification.
MCP_SERVER_CATALOG = {
    # =========================================================================
    # Code Hosting Servers (GitHub / GitLab)
    # =========================================================================
    "github_server": {
        "display_name": "GitHub Server",
        "category": "development",
        "brief": "GitHub code hosting and collaboration API endpoint",
        "prefix": "gh",
    },
    "gitlab_server": {
        "display_name": "GitLab Server",
        "category": "development",
        "brief": "GitLab project and merge workflow API endpoint",
        "prefix": "gl",
    },

    # =========================================================================
    # Team Communication Servers (Slack / Discord)
    # =========================================================================
    "slack_server": {
        "display_name": "Slack Server",
        "category": "communication",
        "brief": "Slack workspace messaging API endpoint",
        "prefix": "slk",
    },
    "discord_server": {
        "display_name": "Discord Server",
        "category": "communication",
        "brief": "Discord server messaging API endpoint",
        "prefix": "dsc",
    },

    # =========================================================================
    # Maps & Navigation Servers (Google Maps / Mapbox)
    # =========================================================================
    "google_maps_server": {
        "display_name": "Google Maps Server",
        "category": "geolocation",
        "brief": "Google Maps routing and geocoding API endpoint",
        "prefix": "gmap",
    },
    "mapbox_server": {
        "display_name": "Mapbox Server",
        "category": "geolocation",
        "brief": "Mapbox geospatial search and routing API endpoint",
        "prefix": "mbx",
    },

    # =========================================================================
    # Search Servers (Brave / Exa)
    # =========================================================================
    "brave_search_server": {
        "display_name": "Brave Search Server",
        "category": "search",
        "brief": "Brave web and local search API endpoint",
        "prefix": "brv",
    },
    "exa_search_server": {
        "display_name": "Exa Search Server",
        "category": "search",
        "brief": "Exa semantic research and code search API endpoint",
        "prefix": "exa",
    },

    # =========================================================================
    # Food Delivery - SINGLE combined server (special case)
    # =========================================================================
    "food_delivery_server": {
        "display_name": "Food Delivery Server",
        "category": "food_delivery",
        "brief": "Combined DoorDash and UberEats ordering API endpoint",
        "prefix": "food",
        "combined": True,
    },
}

# Maps scenario categories to relevant MCP servers
CATEGORY_TO_MCPS = {
    "code_hosting": ["github_server", "gitlab_server"],
    "team_messaging": ["slack_server", "discord_server"],
    "maps": ["google_maps_server", "mapbox_server"],
    "web_search": ["brave_search_server", "exa_search_server"],
    "food_delivery": ["food_delivery_server"],  # Only one server for food
}

# Maps server IDs to their paired alternative (for fallback hints in easy mode)
MCP_PAIRS = {
    "github_server": "gitlab_server",
    "gitlab_server": "github_server",
    "slack_server": "discord_server",
    "discord_server": "slack_server",
    "google_maps_server": "mapbox_server",
    "mapbox_server": "google_maps_server",
    "brave_search_server": "exa_search_server",
    "exa_search_server": "brave_search_server",
    "food_delivery_server": None,  # No pair - it's combined
}


def get_mcp_catalog_for_category(category: str) -> dict:
    """
    Get the MCP catalog filtered to only servers relevant to a category.
    Used internally to know which servers have real APIs behind them.
    """
    server_ids = CATEGORY_TO_MCPS.get(category, [])
    return {
        sid: {
            "display_name": MCP_SERVER_CATALOG[sid]["display_name"],
            "brief": MCP_SERVER_CATALOG[sid]["brief"],
        }
        for sid in server_ids
        if sid in MCP_SERVER_CATALOG
    }


def get_full_mcp_catalog() -> dict:
    """
    Get ALL MCP servers from the catalog.
    The model sees every server, making it harder to guess which one to try.
    """
    return {
        sid: {
            "display_name": info["display_name"],
            "brief": info["brief"],
        }
        for sid, info in MCP_SERVER_CATALOG.items()
    }


def get_mcp_info(mcp_id: str) -> dict:
    """Get full info about a specific MCP server."""
    return MCP_SERVER_CATALOG.get(mcp_id, None)


def get_alternative_mcp(mcp_id: str) -> str:
    """Get the paired alternative MCP for fallback."""
    return MCP_PAIRS.get(mcp_id, None)


def get_server_prefix(mcp_id: str) -> str:
    """Get the tool prefix for a server."""
    info = MCP_SERVER_CATALOG.get(mcp_id)
    if info:
        return info.get("prefix", "")
    return ""


def is_combined_server(mcp_id: str) -> bool:
    """Check if this is a combined server (like food_delivery)."""
    info = MCP_SERVER_CATALOG.get(mcp_id)
    if info:
        return info.get("combined", False)
    return False
