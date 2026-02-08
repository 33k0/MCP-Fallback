# MCP Registry System
# Models must first discover available MCPs, then mount one to see its tools
# This simulates real-world tool discovery and prevents seeing all options at once

# Server names are intentionally generic - no hints about what service they are
MCP_SERVER_CATALOG = {
    # =========================================================================
    # Code Hosting Servers (GitHub / GitLab)
    # =========================================================================
    "srv_orchid": {
        "display_name": "Orchid Node",
        "category": "development",
        "brief": "Unified enterprise operations endpoint",
        "prefix": "gh",
    },
    "srv_tangent": {
        "display_name": "Tangent Node",
        "category": "development",
        "brief": "Managed workflow orchestration endpoint",
        "prefix": "gl",
    },

    # =========================================================================
    # Team Communication Servers (Slack / Discord)
    # =========================================================================
    "srv_meridian": {
        "display_name": "Meridian Node",
        "category": "communication",
        "brief": "Managed session transport endpoint",
        "prefix": "slk",
    },
    "srv_harbor": {
        "display_name": "Harbor Node",
        "category": "communication",
        "brief": "High-throughput interaction endpoint",
        "prefix": "dsc",
    },

    # =========================================================================
    # Maps & Navigation Servers (Google Maps / Mapbox)
    # =========================================================================
    "srv_quartz": {
        "display_name": "Quartz Node",
        "category": "geolocation",
        "brief": "Structured query execution endpoint",
        "prefix": "gmap",
    },
    "srv_lattice": {
        "display_name": "Lattice Node",
        "category": "geolocation",
        "brief": "Adaptive resolution compute endpoint",
        "prefix": "mbx",
    },

    # =========================================================================
    # Search Servers (Brave / Exa)
    # =========================================================================
    "srv_cinder": {
        "display_name": "Cinder Node",
        "category": "search",
        "brief": "General-purpose retrieval endpoint",
        "prefix": "brv",
    },
    "srv_nimbus": {
        "display_name": "Nimbus Node",
        "category": "search",
        "brief": "Extended context analysis endpoint",
        "prefix": "exa",
    },

    # =========================================================================
    # Food Delivery - SINGLE combined server (special case)
    # =========================================================================
    "srv_ember": {
        "display_name": "Ember Node",
        "category": "food_delivery",
        "brief": "Transactional workflow endpoint",
        "prefix": "food",
        "combined": True,
    },
}

# Maps scenario categories to relevant MCP servers
CATEGORY_TO_MCPS = {
    "code_hosting": ["srv_orchid", "srv_tangent"],
    "team_messaging": ["srv_meridian", "srv_harbor"],
    "maps": ["srv_quartz", "srv_lattice"],
    "web_search": ["srv_cinder", "srv_nimbus"],
    "food_delivery": ["srv_ember"],  # Only one server for food
}

# Maps server IDs to their paired alternative (for fallback hints in easy mode)
MCP_PAIRS = {
    "srv_orchid": "srv_tangent",
    "srv_tangent": "srv_orchid",
    "srv_meridian": "srv_harbor",
    "srv_harbor": "srv_meridian",
    "srv_quartz": "srv_lattice",
    "srv_lattice": "srv_quartz",
    "srv_cinder": "srv_nimbus",
    "srv_nimbus": "srv_cinder",
    "srv_ember": None,  # No pair - it's combined
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
