# Hard Mode Controller
# Uses obscured tool names, vague errors, decoy tools, and MCP mounting
# Designed to achieve ~30% success rate

import inspect
import random
from typing import Dict, Any, List

from .tool_obfuscation import (
    TOOL_NAME_MAPPINGS,
    DECOY_TOOLS,
    get_obscured_name,
    get_decoy_response,
    get_decoy_description,
)
from .mcp_registry import (
    MCP_SERVER_CATALOG,
    get_mcp_catalog_description,
    get_alternative_mcp,
)


# Vague error messages that don't clearly indicate "switch services"
VAGUE_ERROR_MESSAGES = [
    {"code": "E_UPSTREAM_TIMEOUT", "message": "Request timed out after 30000ms. The upstream service did not respond in time.", "retry_after": None},
    {"code": "E_RESOURCE_EXHAUSTED", "message": "Resource quota exceeded. Daily limit reached for this endpoint.", "retry_after": "86400s"},
    {"code": "E_MAINTENANCE_WINDOW", "message": "Service temporarily unavailable due to scheduled maintenance.", "retry_after": "3600s"},
    {"code": "E_REGION_UNAVAILABLE", "message": "This service is not available in your region. Geographic restrictions apply.", "retry_after": None},
    {"code": "E_DEPRECATED_ENDPOINT", "message": "This endpoint has been deprecated. Please consult documentation for alternatives.", "retry_after": None},
    {"code": "E_RATE_LIMITED", "message": "Too many requests. Please reduce request frequency.", "retry_after": "60s"},
    {"code": "E_INTERNAL_ERROR", "message": "An unexpected error occurred. Our team has been notified.", "retry_after": None},
    {"code": "E_SERVICE_DEGRADED", "message": "Service is experiencing degraded performance. Some features may be unavailable.", "retry_after": None},
    {"code": "E_CAPACITY_EXCEEDED", "message": "Server capacity exceeded. Request queued for later processing.", "retry_after": "300s"},
    {"code": "E_DEPENDENCY_FAILED", "message": "A downstream dependency failed to respond. Please try again later.", "retry_after": None},
]


def get_random_vague_error() -> dict:
    """Return a random vague error that doesn't scream 'switch services'."""
    error = random.choice(VAGUE_ERROR_MESSAGES)
    return {"error": error}


class ObfuscatedAPI:
    """
    Wraps an API and renames all its methods to obscured versions.
    Also adds decoy tools that do nothing useful.
    """

    def __init__(self, api, prefix: str):
        self.api = api
        self.prefix = prefix
        self._method_map = {}  # obscured_name -> original_method

        # Bind methods with obscured names
        for name, method in inspect.getmembers(api, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue

            # Get obscured name for this method
            original_prefixed = f"{prefix}_{name}"
            obscured = get_obscured_name(name)

            # If no obscured mapping exists, create a simple one
            if obscured == name:
                obscured = f"{prefix[:3]}_{name.replace('_', '')[:12]}"

            self._method_map[obscured] = method
            setattr(self, obscured, method)

        # Add decoy tools for this prefix
        self._add_decoys()

    def _add_decoys(self):
        """Add decoy tools that return useless responses."""
        prefix_short = self.prefix[:3]
        for decoy_name, decoy_info in DECOY_TOOLS.items():
            # Only add decoys that match our prefix
            if decoy_name.startswith(prefix_short) or decoy_name.startswith(self.prefix):
                def make_decoy(info):
                    def decoy_method(**kwargs):
                        return info["response"]
                    decoy_method.__doc__ = info["description"]
                    return decoy_method

                setattr(self, decoy_name, make_decoy(decoy_info))

    def _load_scenario(self, scenario: dict):
        if hasattr(self.api, '_load_scenario'):
            self.api._load_scenario(scenario)


class HardModePairedAPI:
    """
    Combines two APIs with obscured tool names.
    Tools from each service have non-matching names.
    """

    def __init__(self, api_a, prefix_a: str, api_b, prefix_b: str):
        self.api_a = api_a
        self.api_b = api_b
        self.prefix_a = prefix_a
        self.prefix_b = prefix_b

        # Create obscured versions
        self.obscured_a = ObfuscatedAPI(api_a, prefix_a)
        self.obscured_b = ObfuscatedAPI(api_b, prefix_b)

        # Bind all methods from both obscured APIs
        for name in dir(self.obscured_a):
            if name.startswith("_"):
                continue
            attr = getattr(self.obscured_a, name)
            if callable(attr):
                setattr(self, name, attr)

        for name in dir(self.obscured_b):
            if name.startswith("_"):
                continue
            attr = getattr(self.obscured_b, name)
            if callable(attr):
                setattr(self, name, attr)

    def _load_scenario(self, scenario: dict):
        self.obscured_a._load_scenario(scenario)
        self.obscured_b._load_scenario(scenario)


class HardModeErrorInjectedAPI:
    """
    Error injection with vague errors and obscured tool names.
    The model can't pattern-match tool names OR rely on clear error messages.
    """

    def __init__(self, api, fail_methods: list):
        self.api = api
        self.fail_methods = set(fail_methods)
        self.first_call_failed = False
        self.failed_method = None

        # Bind all public methods
        for name in dir(self.api):
            if name.startswith("_"):
                continue
            attr = getattr(self.api, name)
            if not callable(attr):
                continue

            if name in self.fail_methods:
                setattr(self, name, self._make_guarded_method(name, attr))
            else:
                setattr(self, name, attr)

    def _make_guarded_method(self, method_name, original_method):
        def wrapper(*args, **kwargs):
            if not self.first_call_failed:
                self.first_call_failed = True
                self.failed_method = method_name
                # Return a vague error instead of obvious SERVICE_SHUTDOWN
                return get_random_vague_error()
            return original_method(*args, **kwargs)

        wrapper.__doc__ = original_method.__doc__
        if hasattr(original_method, '__signature__'):
            wrapper.__signature__ = original_method.__signature__
        else:
            try:
                wrapper.__signature__ = inspect.signature(original_method)
            except (ValueError, TypeError):
                pass
        wrapper.__name__ = method_name
        return wrapper


class MCPMountingSystem:
    """
    Simulates MCP server discovery and mounting.
    Model must first list available MCPs, then mount one to see tools.
    """

    def __init__(self, available_mcps: Dict[str, Any]):
        """
        Args:
            available_mcps: Dict mapping mcp_id -> API instance
        """
        self.available_mcps = available_mcps
        self.mounted_mcp = None
        self.mounted_api = None

    def list_mcp_servers(self) -> dict:
        """
        List all available MCP servers with brief descriptions.
        Model must call this first to discover what's available.
        """
        servers = []
        for mcp_id, api in self.available_mcps.items():
            info = MCP_SERVER_CATALOG.get(mcp_id, {})
            servers.append({
                "id": mcp_id,
                "name": info.get("display_name", mcp_id),
                "category": info.get("category", "unknown"),
                "description": info.get("brief", "No description"),
            })

        return {
            "available_servers": servers,
            "mounted": self.mounted_mcp,
            "instructions": "Use mcp_mount(server_id) to connect to a server and access its tools.",
        }

    def mcp_mount(self, server_id: str) -> dict:
        """
        Mount an MCP server to access its tools.
        Only one server can be mounted at a time.
        """
        if server_id not in self.available_mcps:
            return {"error": f"Unknown MCP server: {server_id}"}

        self.mounted_mcp = server_id
        self.mounted_api = self.available_mcps[server_id]

        # Get list of available tools
        tools = []
        for name in dir(self.mounted_api):
            if name.startswith("_"):
                continue
            attr = getattr(self.mounted_api, name)
            if callable(attr):
                doc = attr.__doc__ or "No description"
                tools.append({"name": name, "description": doc[:100]})

        return {
            "status": "mounted",
            "server_id": server_id,
            "available_tools": tools,
            "instructions": "You can now call these tools directly.",
        }

    def mcp_unmount(self) -> dict:
        """Unmount the current MCP server."""
        if not self.mounted_mcp:
            return {"error": "No MCP server is currently mounted"}

        old_mcp = self.mounted_mcp
        self.mounted_mcp = None
        self.mounted_api = None

        return {
            "status": "unmounted",
            "previous_server": old_mcp,
        }

    def get_mounted_tools(self) -> list:
        """Get tool schemas for the currently mounted MCP."""
        if not self.mounted_api:
            return []

        tools = []
        for name in dir(self.mounted_api):
            if name.startswith("_"):
                continue
            attr = getattr(self.mounted_api, name)
            if callable(attr):
                tools.append({
                    "name": name,
                    "method": attr,
                })
        return tools


# =============================================================================
# Hard Mode Factory Functions
# =============================================================================

def make_hard_mode_code_hosting(github_api, gitlab_api):
    """Create hard mode code hosting with obscured names and vague errors."""
    paired = HardModePairedAPI(github_api, "gh", gitlab_api, "gl")

    # Map obscured fail methods
    fail_methods = [
        "gh_ticket_submit", "gl_workitem_new",  # create issue
        "gh_changeset_propose", "gl_diff_request",  # create PR
        "gh_project_lookup", "gl_namespace_search",  # search repos
        "gh_repo_clone_remote", "gl_project_duplicate",  # fork
    ]

    return HardModeErrorInjectedAPI(paired, fail_methods)


def make_hard_mode_team_messaging(slack_api, discord_api):
    """Create hard mode team messaging with obscured names and vague errors."""
    paired = HardModePairedAPI(slack_api, "slk", discord_api, "dsc")

    fail_methods = [
        "slk_broadcast_text", "dsc_chat_post",  # send message
        "slk_emoji_attach", "dsc_emote_add",  # add reaction
        "slk_timeline_fetch", "dsc_log_retrieve",  # get history
    ]

    return HardModeErrorInjectedAPI(paired, fail_methods)


def make_hard_mode_maps(google_maps_api, mapbox_api):
    """Create hard mode maps with obscured names and vague errors."""
    paired = HardModePairedAPI(google_maps_api, "gmap", mapbox_api, "mbx")

    fail_methods = [
        "gmap_path_calculate", "mbx_route_compute",  # directions
        "gmap_coords_resolve", "mbx_location_encode",  # geocode
        "gmap_poi_query", "mbx_feature_search",  # places
    ]

    return HardModeErrorInjectedAPI(paired, fail_methods)


def make_hard_mode_web_search(brave_api, exa_api):
    """Create hard mode web search with obscured names and vague errors."""
    paired = HardModePairedAPI(brave_api, "brv", exa_api, "exa")

    fail_methods = [
        "brv_index_query", "exa_corpus_search",  # web search
        "exa_codebase_context",  # code search
        "exa_org_intelligence",  # company research
    ]

    return HardModeErrorInjectedAPI(paired, fail_methods)


def make_hard_mode_food_delivery(food_api):
    """Create hard mode food delivery with obscured names and vague errors."""
    obscured = ObfuscatedAPI(food_api, "delivery")

    fail_methods = [
        "ue_transaction_submit", "dd_checkout_complete",  # place order
        "ue_fulfillment_track", "dd_delivery_status",  # check status
    ]

    return HardModeErrorInjectedAPI(obscured, fail_methods)
