# Error Injection Controller - Wraps mock APIs, injects failures on first call
# Uses obfuscated tool names and vague error messages for all difficulty levels

import inspect
import random

from .tool_obfuscation import DECOY_TOOLS


# =============================================================================
# Vague error messages - don't clearly indicate "switch services"
# =============================================================================

VAGUE_ERRORS = [
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


def get_vague_error() -> dict:
    """Return a random vague error message."""
    error = random.choice(VAGUE_ERRORS)
    return {"error": error}


class ObfuscatedPairedAPI:
    """
    Combines TWO separate API instances into one with OBFUSCATED method names.
    Tools from each service have non-matching, realistic but obscure names.
    Also injects decoy tools that do nothing useful.
    """

    def __init__(self, api_a, prefix_a: str, api_b, prefix_b: str, name_map_a: dict, name_map_b: dict):
        """
        Args:
            api_a: First API instance
            prefix_a: Short prefix for first API (e.g., "gh")
            api_b: Second API instance
            prefix_b: Short prefix for second API (e.g., "gl")
            name_map_a: Dict mapping original method names to obfuscated names for API A
            name_map_b: Dict mapping original method names to obfuscated names for API B
        """
        self.api_a = api_a
        self.api_b = api_b
        self.prefix_a = prefix_a
        self.prefix_b = prefix_b
        self.name_map_a = name_map_a
        self.name_map_b = name_map_b

        # Bind methods from API A with obfuscated names
        for name, method in inspect.getmembers(api_a, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            obfuscated = name_map_a.get(name, f"{prefix_a}_{name}")
            setattr(self, obfuscated, method)

        # Bind methods from API B with obfuscated names
        for name, method in inspect.getmembers(api_b, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            obfuscated = name_map_b.get(name, f"{prefix_b}_{name}")
            setattr(self, obfuscated, method)

        # Add decoy tools
        self._add_decoys(prefix_a)
        self._add_decoys(prefix_b)

    def _add_decoys(self, prefix: str):
        """Add decoy tools that return useless responses."""
        for decoy_name, decoy_info in DECOY_TOOLS.items():
            if decoy_name.startswith(prefix):
                def make_decoy(info):
                    def decoy_method(**kwargs):
                        return info["response"]
                    decoy_method.__doc__ = info["description"]
                    return decoy_method
                setattr(self, decoy_name, make_decoy(decoy_info))

    def _load_scenario(self, scenario: dict):
        """Load scenario into both APIs."""
        if hasattr(self.api_a, '_load_scenario'):
            self.api_a._load_scenario(scenario)
        if hasattr(self.api_b, '_load_scenario'):
            self.api_b._load_scenario(scenario)


class ErrorInjectedAPI:
    """
    Error injection wrapper with VAGUE error messages.
    The FIRST service called will PERMANENTLY fail - model must switch to alternative.
    """

    def __init__(self, api, fail_methods: list):
        """
        Args:
            api: The underlying mock API instance.
            fail_methods (list): List of method names that can fail.
        """
        self.api = api
        self.fail_methods = set(fail_methods)
        self.permanently_failed_methods = set()  # Methods that always fail
        self.first_failure_recorded = False

        # Bind ALL public methods from the underlying API
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
        """Wrapper that permanently fails the first service tried."""
        def wrapper(*args, **kwargs):
            # If this method is in the permanently failed set, always fail
            if method_name in self.permanently_failed_methods:
                return get_vague_error()

            # If no failure recorded yet, this becomes the permanently failed service
            if not self.first_failure_recorded:
                self.first_failure_recorded = True
                # Mark ALL methods from this service as permanently failed
                # Detect service by prefix (e.g., "gh_", "gl_", "slk_", "dsc_")
                prefix = method_name.split("_")[0] + "_"
                for m in self.fail_methods:
                    if m.startswith(prefix):
                        self.permanently_failed_methods.add(m)
                return get_vague_error()

            # Otherwise, this is the alternative service - let it work
            return original_method(*args, **kwargs)

        wrapper.__doc__ = original_method.__doc__
        try:
            wrapper.__signature__ = inspect.signature(original_method)
        except (ValueError, TypeError):
            pass
        wrapper.__name__ = method_name
        return wrapper


# =============================================================================
# Obfuscated name mappings for each service
# =============================================================================

GITHUB_NAME_MAP = {
    "create_issue": "gh_ticket_submit",
    "create_pull_request": "gh_changeset_propose",
    "search_repositories": "gh_project_lookup",
    "fork_repository": "gh_repo_duplicate",
    "list_issues": "gh_ticket_enumerate",
    "get_issue": "gh_ticket_fetch",
    "update_issue": "gh_ticket_modify",
    "add_issue_comment": "gh_ticket_annotate",
    "create_branch": "gh_ref_create",
    "list_branches": "gh_refs_enumerate",
    "get_file_contents": "gh_blob_retrieve",
    "push_files": "gh_tree_update",
    "list_commits": "gh_revisions_list",
    "get_pull_request": "gh_changeset_fetch",
    "list_pull_requests": "gh_changesets_enumerate",
    "merge_pull_request": "gh_changeset_integrate",
}

GITLAB_NAME_MAP = {
    "create_issue": "gl_workitem_new",
    "create_merge_request": "gl_diff_request",
    "search_repositories": "gl_namespace_query",
    "fork_repository": "gl_project_fork",
    "list_issues": "gl_workitems_list",
    "get_issue": "gl_workitem_read",
    "create_branch": "gl_branch_init",
    "list_merge_requests": "gl_diffs_pending",
    "get_merge_request": "gl_diff_details",
}

SLACK_NAME_MAP = {
    "slack_post_message": "slk_broadcast_text",
    "slack_add_reaction": "slk_emoji_attach",
    "slack_get_channel_history": "slk_timeline_fetch",
    "slack_list_channels": "slk_rooms_enumerate",
    "slack_reply_to_thread": "slk_thread_continue",
    "slack_get_thread_replies": "slk_thread_read",
    "slack_get_users": "slk_members_list",
    "slack_get_user_profile": "slk_member_info",
}

DISCORD_NAME_MAP = {
    "send_message": "dsc_chat_post",
    "add_reaction": "dsc_emote_add",
    "read_messages": "dsc_log_retrieve",
    "list_channels": "dsc_rooms_scan",
    "edit_message": "dsc_chat_revise",
    "delete_message": "dsc_chat_purge",
    "send_private_message": "dsc_whisper_send",
    "create_text_channel": "dsc_room_create",
    "get_server_info": "dsc_guild_stats",
    "get_user_id_by_name": "dsc_player_lookup",
}

GOOGLE_MAPS_NAME_MAP = {
    "maps_geocode": "gmap_coords_resolve",
    "maps_reverse_geocode": "gmap_addr_from_point",
    "maps_directions": "gmap_path_calculate",
    "maps_distance_matrix": "gmap_distances_batch",
    "maps_search_places": "gmap_poi_query",
    "maps_place_details": "gmap_poi_details",
    "maps_elevation": "gmap_altitude_check",
}

MAPBOX_NAME_MAP = {
    "mapbox_geocode": "mbx_location_encode",
    "mapbox_reverse_geocode": "mbx_point_decode",
    "mapbox_directions": "mbx_route_compute",
    "mapbox_matrix": "mbx_distances_matrix",
    "mapbox_search_places": "mbx_feature_search",
    "mapbox_isochrone": "mbx_reachability_zone",
    "mapbox_bearing": "mbx_heading_calc",
    "mapbox_distance": "mbx_haversine_dist",
    "mapbox_midpoint": "mbx_center_find",
    "mapbox_destination": "mbx_endpoint_project",
}

BRAVE_NAME_MAP = {
    "brave_web_search": "brv_index_query",
    "brave_local_search": "brv_nearby_lookup",
}

EXA_NAME_MAP = {
    "web_search_exa": "exa_corpus_search",
    "get_contents_exa": "exa_doc_extract",
    "find_similar_exa": "exa_similarity_find",
    "get_code_context_exa": "exa_codebase_query",
    "research_topic_exa": "exa_topic_deep_dive",
    "company_research_exa": "exa_org_intelligence",
    "people_search_exa": "exa_person_lookup",
    "deep_search_exa": "exa_comprehensive_scan",
    "research_paper_search_exa": "exa_academic_query",
}

UBEREATS_NAME_MAP = {
    "ubereats_search_restaurants": "ue_vendor_discover",
    "ubereats_get_menu": "ue_catalog_fetch",
    "ubereats_place_order": "ue_transaction_submit",
    "ubereats_get_order_status": "ue_fulfillment_track",
    "ubereats_login": "ue_session_init",
}

DOORDASH_NAME_MAP = {
    "doordash_find_restaurants": "dd_merchant_search",
    "doordash_view_menu": "dd_offerings_list",
    "doordash_submit_order": "dd_checkout_complete",
    "doordash_check_order_status": "dd_delivery_status",
    "doordash_authenticate": "dd_auth_handshake",
}


# =============================================================================
# Factory functions with obfuscation and vague errors
# =============================================================================

def make_error_injected_code_hosting(github_api, gitlab_api):
    """Create code hosting API with obfuscated names and vague errors."""
    paired = ObfuscatedPairedAPI(
        github_api, "gh", gitlab_api, "gl",
        GITHUB_NAME_MAP, GITLAB_NAME_MAP
    )

    fail_methods = [
        "gh_ticket_submit", "gl_workitem_new",
        "gh_changeset_propose", "gl_diff_request",
        "gh_project_lookup", "gl_namespace_query",
        "gh_repo_duplicate", "gl_project_fork",
    ]

    return ErrorInjectedAPI(paired, fail_methods)


def make_error_injected_team_messaging(slack_api, discord_api):
    """Create team messaging API with obfuscated names and vague errors."""
    paired = ObfuscatedPairedAPI(
        slack_api, "slk", discord_api, "dsc",
        SLACK_NAME_MAP, DISCORD_NAME_MAP
    )

    fail_methods = [
        "slk_broadcast_text", "dsc_chat_post",
        "slk_emoji_attach", "dsc_emote_add",
        "slk_timeline_fetch", "dsc_log_retrieve",
    ]

    return ErrorInjectedAPI(paired, fail_methods)


def make_error_injected_maps(google_maps_api, mapbox_api):
    """Create maps API with obfuscated names and vague errors."""
    paired = ObfuscatedPairedAPI(
        google_maps_api, "gmap", mapbox_api, "mbx",
        GOOGLE_MAPS_NAME_MAP, MAPBOX_NAME_MAP
    )

    fail_methods = [
        "gmap_path_calculate", "mbx_route_compute",
        "gmap_coords_resolve", "mbx_location_encode",
        "gmap_poi_query", "mbx_feature_search",
    ]

    return ErrorInjectedAPI(paired, fail_methods)


def make_error_injected_web_search(brave_api, exa_api):
    """Create web search API with obfuscated names and vague errors."""
    paired = ObfuscatedPairedAPI(
        brave_api, "brv", exa_api, "exa",
        BRAVE_NAME_MAP, EXA_NAME_MAP
    )

    fail_methods = [
        "brv_index_query", "exa_corpus_search",
        "exa_codebase_query", "exa_org_intelligence",
    ]

    return ErrorInjectedAPI(paired, fail_methods)


def make_error_injected_food_delivery(food_api):
    """Create food delivery API with obfuscated names and vague errors."""
    # Food delivery is already a paired API internally, so we handle it differently
    # We need to wrap it with obfuscation

    class ObfuscatedFoodAPI:
        def __init__(self, api):
            self.api = api
            # Map old names to new obfuscated names
            method_map = {
                "ubereats_login": "ue_session_init",
                "ubereats_search_restaurants": "ue_vendor_discover",
                "ubereats_get_menu": "ue_catalog_fetch",
                "ubereats_place_order": "ue_transaction_submit",
                "ubereats_get_order_status": "ue_fulfillment_track",
                "doordash_authenticate": "dd_auth_handshake",
                "doordash_find_restaurants": "dd_merchant_search",
                "doordash_view_menu": "dd_offerings_list",
                "doordash_submit_order": "dd_checkout_complete",
                "doordash_check_order_status": "dd_delivery_status",
            }

            for old_name, new_name in method_map.items():
                if hasattr(api, old_name):
                    method = getattr(api, old_name)
                    setattr(self, new_name, method)

            # Add decoys
            for decoy_name, decoy_info in DECOY_TOOLS.items():
                if decoy_name.startswith("ue_") or decoy_name.startswith("dd_"):
                    def make_decoy(info):
                        def decoy_method(**kwargs):
                            return info["response"]
                        decoy_method.__doc__ = info["description"]
                        return decoy_method
                    setattr(self, decoy_name, make_decoy(decoy_info))

        def _load_scenario(self, scenario):
            if hasattr(self.api, '_load_scenario'):
                self.api._load_scenario(scenario)

    obfuscated = ObfuscatedFoodAPI(food_api)

    fail_methods = [
        "ue_transaction_submit", "dd_checkout_complete",
        "ue_fulfillment_track", "dd_delivery_status",
    ]

    return ErrorInjectedAPI(obfuscated, fail_methods)


# =============================================================================
# MCP Mounting System - Hide tools until server is mounted
# =============================================================================

class MCPMountingSystem:
    """
    Simulates MCP server discovery and mounting.
    Model sees only server descriptions initially, must mount to see tools.
    Only ONE server can be mounted at a time (except for combined servers).
    """

    def __init__(self, server_apis: dict, category: str):
        """
        Args:
            server_apis: Dict mapping server_id -> (api_instance, tool_prefix)
            category: The scenario category (e.g., "code_hosting")
        """
        self.server_apis = server_apis  # {server_id: (api, prefix)}
        self.category = category
        self.mounted_server = None
        self.mounted_api = None
        self.failed_servers = set()  # Track which servers have failed

        # Import here to avoid circular imports
        from .mcp_registry import get_mcp_catalog_for_category, is_combined_server
        self.catalog = get_mcp_catalog_for_category(category)
        self.is_combined_server = is_combined_server

    def mcp_list_servers(self) -> dict:
        """
        List all available MCP servers for this category.
        This is what the model sees BEFORE mounting any server.
        """
        servers = []
        for server_id, info in self.catalog.items():
            servers.append({
                "server_id": server_id,
                "name": info["display_name"],
                "description": info["brief"],
                "status": "failed" if server_id in self.failed_servers else "available",
            })

        return {
            "available_servers": servers,
            "currently_mounted": self.mounted_server,
            "instructions": "Use mcp_mount(server_id) to connect to a server and see its tools. Use mcp_unmount() to disconnect before switching servers.",
        }

    def mcp_mount(self, server_id: str) -> dict:
        """
        Mount an MCP server to access its tools.
        Returns the list of available tools on that server.
        """
        if server_id not in self.server_apis:
            return {"error": f"Unknown server: {server_id}. Use mcp_list_servers() to see available servers."}

        if self.mounted_server is not None and not self.is_combined_server(self.mounted_server):
            return {"error": f"Server '{self.mounted_server}' is already mounted. Use mcp_unmount() first."}

        self.mounted_server = server_id
        self.mounted_api = self.server_apis[server_id][0]

        # Get list of available tools (methods) on this server
        tools = []
        for name in dir(self.mounted_api):
            if name.startswith("_"):
                continue
            attr = getattr(self.mounted_api, name)
            if callable(attr):
                doc = getattr(attr, '__doc__', None) or "No description available"
                tools.append({
                    "tool_name": name,
                    "description": doc[:100] + "..." if len(doc) > 100 else doc,
                })

        return {
            "status": "mounted",
            "server_id": server_id,
            "server_name": self.catalog[server_id]["display_name"],
            "tools_available": tools,
            "tool_count": len(tools),
            "instructions": "You can now call these tools directly. If tools fail, consider using mcp_unmount() and trying a different server.",
        }

    def mcp_unmount(self) -> dict:
        """Unmount the current server to switch to a different one."""
        if self.mounted_server is None:
            return {"error": "No server is currently mounted."}

        old_server = self.mounted_server
        self.mounted_server = None
        self.mounted_api = None

        return {
            "status": "unmounted",
            "previous_server": old_server,
            "instructions": "Use mcp_list_servers() to see available servers, then mcp_mount(server_id) to connect to a new one.",
        }

    def mark_server_failed(self, server_id: str):
        """Mark a server as failed (called when error injection triggers)."""
        self.failed_servers.add(server_id)

    def get_current_tools(self) -> list:
        """Get the tools available on the currently mounted server."""
        if self.mounted_api is None:
            return []

        tools = []
        for name in dir(self.mounted_api):
            if name.startswith("_"):
                continue
            attr = getattr(self.mounted_api, name)
            if callable(attr):
                tools.append((name, attr))
        return tools

    def call_tool(self, tool_name: str, **kwargs):
        """Call a tool on the mounted server."""
        if self.mounted_api is None:
            return {"error": "No server is mounted. Use mcp_mount(server_id) first."}

        if not hasattr(self.mounted_api, tool_name):
            return {"error": f"Tool '{tool_name}' not found on server '{self.mounted_server}'."}

        method = getattr(self.mounted_api, tool_name)
        return method(**kwargs)


class MountableErrorInjectedAPI:
    """
    Wrapper that combines MCP mounting with error injection.
    First server mounted and used will permanently fail.
    """

    def __init__(self, mounting_system: MCPMountingSystem, fail_prefixes: list):
        """
        Args:
            mounting_system: The MCPMountingSystem instance
            fail_prefixes: List of tool prefixes that can fail (e.g., ["gh_", "gl_"])
        """
        self.mounting = mounting_system
        self.fail_prefixes = fail_prefixes
        self.failed_prefix = None  # The prefix that permanently fails
        self.first_failure_recorded = False

    def mcp_list_servers(self) -> dict:
        return self.mounting.mcp_list_servers()

    def mcp_mount(self, server_id: str) -> dict:
        return self.mounting.mcp_mount(server_id)

    def mcp_unmount(self) -> dict:
        return self.mounting.mcp_unmount()

    def call_tool(self, tool_name: str, **kwargs):
        """Call a tool with error injection."""
        # Check if this tool's prefix has failed
        for prefix in self.fail_prefixes:
            if tool_name.startswith(prefix):
                if self.failed_prefix == prefix:
                    # This prefix is permanently failed
                    return get_vague_error()

                if not self.first_failure_recorded:
                    # First call to a fail-able tool - mark this prefix as failed
                    self.first_failure_recorded = True
                    self.failed_prefix = prefix
                    # Mark the server as failed in mounting system
                    self.mounting.mark_server_failed(self.mounting.mounted_server)
                    return get_vague_error()

        # Not a failed prefix, call normally
        return self.mounting.call_tool(tool_name, **kwargs)


# =============================================================================
# Legacy classes for backward compatibility
# =============================================================================

class PairedServerAPI:
    """Legacy class - use ObfuscatedPairedAPI instead."""

    def __init__(self, api_a, prefix_a: str, api_b, prefix_b: str):
        self.api_a = api_a
        self.api_b = api_b
        self.prefix_a = prefix_a
        self.prefix_b = prefix_b

        for name, method in inspect.getmembers(api_a, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            prefixed_name = f"{prefix_a}_{name}"
            setattr(self, prefixed_name, method)

        for name, method in inspect.getmembers(api_b, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            prefixed_name = f"{prefix_b}_{name}"
            setattr(self, prefixed_name, method)

    def _load_scenario(self, scenario: dict):
        if hasattr(self.api_a, '_load_scenario'):
            self.api_a._load_scenario(scenario)
        if hasattr(self.api_b, '_load_scenario'):
            self.api_b._load_scenario(scenario)
