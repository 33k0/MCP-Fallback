import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import inspect
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Set, get_type_hints

from mock_servers.food_delivery_api import FoodDeliveryAPI
from mock_servers.github_api import GitHubAPI
from mock_servers.gitlab_api import GitLabAPI
from mock_servers.brave_search_api import BraveSearchAPI
from mock_servers.exa_search_api import ExaSearchAPI
from mock_servers.slack_api import SlackAPI
from mock_servers.discord_api import DiscordAPI
from mock_servers.google_maps_api import GoogleMapsAPI
from mock_servers.mapbox_api import MapboxAPI

from error_injection.controller import (
    ErrorInjectedAPI,
    PairedServerAPI,
    MCPMountingSystem,
    MountableErrorInjectedAPI,
    make_error_injected_food_delivery,
    make_error_injected_code_hosting,
    make_error_injected_web_search,
    make_error_injected_team_messaging,
    make_error_injected_maps,
    GITHUB_NAME_MAP,
    GITLAB_NAME_MAP,
    SLACK_NAME_MAP,
    DISCORD_NAME_MAP,
    GOOGLE_MAPS_NAME_MAP,
    MAPBOX_NAME_MAP,
    BRAVE_NAME_MAP,
    EXA_NAME_MAP,
)
from error_injection.mcp_registry import get_mcp_catalog_for_category, get_full_mcp_catalog
from error_injection.tool_obfuscation import DECOY_TOOLS


PROMPTS_FILE = os.path.join(PROJECT_ROOT, "scenarios", "prompts.json")

DEFAULT_MODELS = {
    "openai": "gpt-5.2",
    "anthropic": "claude-sonnet-4-5-20250929",
    "google": "gemini-2.5-pro",
}

SCENARIO_TO_SERVER = {
    "food_delivery_order": "food_delivery",
    "food_delivery_status": "food_delivery",
    "code_hosting_create_issue": "code_hosting",
    "code_hosting_fork_repo": "code_hosting",
    "code_hosting_create_pr": "code_hosting",
    "code_hosting_search_repos": "code_hosting",
    "web_search_general": "web_search",
    "web_search_code": "web_search",
    "web_search_company": "web_search",
    "team_messaging_send": "team_messaging",
    "team_messaging_react": "team_messaging",
    "team_messaging_history": "team_messaging",
    "maps_directions": "maps",
    "maps_geocode": "maps",
    "maps_places": "maps",
}

MCP_REGISTRY = {
    "food_delivery":    lambda: make_error_injected_food_delivery(FoodDeliveryAPI()),
    "code_hosting":     lambda: make_error_injected_code_hosting(GitHubAPI(), GitLabAPI()),
    "web_search":       lambda: make_error_injected_web_search(BraveSearchAPI(), ExaSearchAPI()),
    "team_messaging":   lambda: make_error_injected_team_messaging(SlackAPI(), DiscordAPI()),
    "maps":             lambda: make_error_injected_maps(GoogleMapsAPI(), MapboxAPI()),
}

SUCCESS_CRITERIA = {
    "food_delivery_order": [
        ("ue_transaction_submit", "order_id"), ("dd_checkout_complete", "confirmation_number"),
    ],
    "food_delivery_status": [
        ("ue_fulfillment_track", "status"), ("dd_delivery_status", "order_status"),
    ],
    "code_hosting_create_issue": [
        ("gh_ticket_submit", "number"), ("gl_workitem_new", "iid"),
    ],
    "code_hosting_fork_repo": [
        ("gh_repo_duplicate", "full_name"), ("gl_project_fork", "id"),
    ],
    "code_hosting_create_pr": [
        ("gh_changeset_propose", "number"), ("gl_diff_request", "iid"),
    ],
    "code_hosting_search_repos": [
        ("gh_project_lookup", "total_count"), ("gl_namespace_query", "total_count"),
    ],
    "web_search_general": [
        ("brv_index_query", "results"), ("exa_corpus_search", "results"),
    ],
    "web_search_code": [
        ("brv_index_query", "results"), ("exa_codebase_query", "results"),
    ],
    "web_search_company": [
        ("brv_index_query", "results"), ("exa_org_intelligence", "found"),
    ],
    "team_messaging_send": [
        ("slk_broadcast_text", "ts"), ("dsc_chat_post", "message"),
    ],
    "team_messaging_react": [
        ("slk_emoji_attach", "ok"), ("dsc_emote_add", "success"),
    ],
    "team_messaging_history": [
        ("slk_timeline_fetch", "messages"), ("dsc_log_retrieve", "messages"),
    ],
    "maps_directions": [
        ("gmap_path_calculate", "routes"), ("mbx_route_compute", "routes"),
    ],
    "maps_geocode": [
        ("gmap_coords_resolve", "results"), ("mbx_location_encode", "features"),
    ],
    "maps_places": [
        ("gmap_poi_query", "results"), ("mbx_feature_search", "features"),
    ],
}

WORKFLOW_PREREQS = {
    "food_delivery_order": {
        "dd_checkout_complete": [["dd_auth_handshake"], ["dd_merchant_search"], ["dd_offerings_list"]],
        "ue_transaction_submit": [["ue_session_init"], ["ue_vendor_discover"], ["ue_catalog_fetch"]],
    },
    "food_delivery_status": {
        "dd_delivery_status": [["dd_auth_handshake"]],
        "ue_fulfillment_track": [["ue_session_init"]],
    },
    "code_hosting_create_issue": {
        "gh_ticket_submit": [["gh_project_lookup"]],
        "gl_workitem_new": [["gl_namespace_query"]],
    },
    "code_hosting_fork_repo": {
        "gh_repo_duplicate": [["gh_project_lookup"]],
        "gl_project_fork": [["gl_namespace_query"]],
    },
    "code_hosting_create_pr": {
        "gh_changeset_propose": [["gh_project_lookup"]],
        "gl_diff_request": [["gl_namespace_query"]],
    },
    "code_hosting_search_repos": {
        "gh_project_lookup": [],
        "gl_namespace_query": [],
    },
    "web_search_general": {
        "brv_index_query": [],
        "exa_corpus_search": [],
    },
    "web_search_code": {
        "brv_index_query": [],
        "exa_codebase_query": [],
    },
    "web_search_company": {
        "brv_index_query": [],
        "exa_org_intelligence": [],
    },
    "team_messaging_send": {
        "slk_broadcast_text": [["slk_rooms_enumerate", "slk_timeline_fetch"]],
        "dsc_chat_post": [["dsc_rooms_scan", "dsc_log_retrieve"]],
    },
    "team_messaging_react": {
        "slk_emoji_attach": [["slk_timeline_fetch"]],
        "dsc_emote_add": [["dsc_log_retrieve"]],
    },
    "team_messaging_history": {
        "slk_timeline_fetch": [["slk_rooms_enumerate"]],
        "dsc_log_retrieve": [["dsc_rooms_scan"]],
    },
    "maps_directions": {
        "gmap_path_calculate": [["gmap_coords_resolve", "gmap_poi_query"]],
        "mbx_route_compute": [["mbx_location_encode", "mbx_feature_search"]],
    },
    "maps_geocode": {
        "gmap_coords_resolve": [],
        "mbx_location_encode": [],
    },
    "maps_places": {
        "gmap_poi_query": [["gmap_coords_resolve"]],
        "mbx_feature_search": [["mbx_location_encode"]],
    },
}

REFRESH_TOOLS = {
    "dd_merchant_search", "ue_vendor_discover",
    "gh_project_lookup", "gl_namespace_query",
    "slk_timeline_fetch", "dsc_log_retrieve",
    "gmap_coords_resolve", "mbx_location_encode",
    "gmap_poi_query", "mbx_feature_search",
    "brv_index_query", "exa_corpus_search", "exa_codebase_query", "exa_org_intelligence",
}

CANONICAL_TOOL_ALIASES = {
    "gh_ticket_submit": "record_create",
    "gl_workitem_new": "record_create",
    "gh_changeset_propose": "change_request_create",
    "gl_diff_request": "change_request_create",
    "gh_project_lookup": "workspace_search",
    "gl_namespace_query": "workspace_search",
    "gh_repo_duplicate": "workspace_clone",
    "gl_project_fork": "workspace_clone",
    "slk_broadcast_text": "message_publish",
    "dsc_chat_post": "message_publish",
    "slk_emoji_attach": "reaction_apply",
    "dsc_emote_add": "reaction_apply",
    "slk_timeline_fetch": "message_history_read",
    "dsc_log_retrieve": "message_history_read",
    "gmap_path_calculate": "route_plan",
    "mbx_route_compute": "route_plan",
    "gmap_coords_resolve": "location_resolve",
    "mbx_location_encode": "location_resolve",
    "gmap_poi_query": "places_discover",
    "mbx_feature_search": "places_discover",
    "brv_index_query": "knowledge_search",
    "exa_corpus_search": "knowledge_search",
    "exa_codebase_query": "code_search",
    "exa_org_intelligence": "organization_research",
    "dd_checkout_complete": "order_commit",
    "ue_transaction_submit": "order_commit",
    "dd_delivery_status": "delivery_status_check",
    "ue_fulfillment_track": "delivery_status_check",
    "dd_merchant_search": "vendor_discover",
    "ue_vendor_discover": "vendor_discover",
    "dd_offerings_list": "catalog_fetch",
    "ue_catalog_fetch": "catalog_fetch",
    "dd_auth_handshake": "session_auth",
    "ue_session_init": "session_auth",
}


def create_client(provider: str):
    """Create an API client for the specified provider."""
    if provider == "openai":
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        return OpenAI(api_key=api_key)
    elif provider == "anthropic":
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        return anthropic.Anthropic(api_key=api_key)
    elif provider == "google":
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set")
        genai.configure(api_key=api_key)
        return genai
    else:
        raise ValueError(f"Unknown provider: {provider}")


def coerce_args(fn, args: dict) -> dict:
    sig = inspect.signature(fn)
    hints = {}
    try:
        hints = get_type_hints(fn)
    except Exception:
        pass

    coerced = {}
    for param_name, param in sig.parameters.items():
        if param_name not in args:
            continue
        value = args[param_name]
        annotation = hints.get(param_name, param.annotation)
        coerced[param_name] = _coerce_value(value, annotation)

    return coerced


def _coerce_value(value, annotation):
    if annotation is inspect.Parameter.empty or annotation is Any:
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (list, dict)):
                value = parsed
        except (json.JSONDecodeError, TypeError):
            pass

    origin = getattr(annotation, "__origin__", None)

    if annotation is int:
        return int(value)
    elif annotation is float:
        return float(value)
    elif annotation is bool:
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    elif annotation is str:
        return str(value)
    elif origin is list:
        if isinstance(value, list):
            inner_args = getattr(annotation, "__args__", None)
            if inner_args:
                return [_coerce_value(item, inner_args[0]) for item in value]
            return value
        return value
    elif origin is dict:
        return value

    return value


def _param_to_json_schema(param) -> dict:
    annotation = param.annotation
    if annotation is inspect.Parameter.empty:
        return {"type": "string"}

    origin = getattr(annotation, "__origin__", None)

    if annotation is int:
        return {"type": "integer"}
    elif annotation is float:
        return {"type": "number"}
    elif annotation is bool:
        return {"type": "boolean"}
    elif annotation is str:
        return {"type": "string"}
    elif origin is list:
        inner_args = getattr(annotation, "__args__", None)
        if inner_args:
            inner = _annotation_to_json_schema(inner_args[0])
            return {"type": "array", "items": inner}
        return {"type": "array"}
    elif origin is dict:
        return {"type": "object"}

    return {"type": "string"}


def _annotation_to_json_schema(annotation) -> dict:
    origin = getattr(annotation, "__origin__", None)
    if annotation is int:
        return {"type": "integer"}
    elif annotation is float:
        return {"type": "number"}
    elif annotation is bool:
        return {"type": "boolean"}
    elif annotation is str:
        return {"type": "string"}
    elif origin is dict:
        return {"type": "object"}
    elif origin is list:
        return {"type": "array"}
    return {"type": "string"}


class MCPRunner:
    """
    Runs a single benchmark scenario. Supports OpenAI, Anthropic, and Google.
    Uses MCP mounting - model must mount a server before seeing its tools.
    """

    def __init__(self, model_client, model_name: str, server_name: str, provider: str = "openai", level: str = "easy", verbose: bool = True, scenario_name: str = None):
        self.model = model_client
        self.model_name = model_name
        self.server_name = server_name
        self.scenario_name = scenario_name or server_name
        self.provider = provider
        self.level = level
        self.verbose = verbose

        self.active_api = None
        self.trace = []
        self.conversation = []
        self.success = False
        self.failure_reason = None
        self.hit_error = False
        self.switched_service = False

        
        self.mounted_server_id = None
        self.mounted_tools = {}  
        self.mounted_alias_to_real = {}  
        self.mounted_real_to_alias = {}  
        self.server_catalog = get_full_mcp_catalog()
        self.scenario_server_ids = set(get_mcp_catalog_for_category(server_name).keys())
        self.server_apis = {} 
        self.failed_prefix = None 
        self.first_failure_recorded = False

        self.recent_responses = []
        self.max_repeats = 2

        self.max_retries_per_failing_tool = 2
        self.failing_tool_attempts = {}

        self.injected_error_count = 0
        self.decoy_calls = 0
        self.decoy_cost_usd = 0.0
        self.max_decoy_calls = 2
        self.max_decoy_cost_usd = 2.5
        self.disqualified = False
        self.disqualify_reason = None
        self.requires_fresh_resolution = False
        self.mount_miss_count = 0
        self.max_mount_misses = 3
        self.commentary_after_error_turns = 0
        self.max_commentary_after_error_turns = 3

    def _init_servers(self):
        """Initialize all server APIs for this category (but don't expose tools yet)."""
        if self.server_name == "food_delivery":
            api = make_error_injected_food_delivery(FoodDeliveryAPI())
            api.api._load_scenario({})
            self.server_apis["food_delivery_server"] = api
        elif self.server_name == "code_hosting":
            gh_api = make_error_injected_code_hosting(GitHubAPI(), GitLabAPI())
            gh_api.api._load_scenario({})
            self.server_apis["github_server"] = ("gh", gh_api)
            self.server_apis["gitlab_server"] = ("gl", gh_api)
        elif self.server_name == "team_messaging":
            api = make_error_injected_team_messaging(SlackAPI(), DiscordAPI())
            api.api._load_scenario({})
            self.server_apis["slack_server"] = ("slk", api)
            self.server_apis["discord_server"] = ("dsc", api)
        elif self.server_name == "maps":
            api = make_error_injected_maps(GoogleMapsAPI(), MapboxAPI())
            api.api._load_scenario({})
            self.server_apis["google_maps_server"] = ("gmap", api)
            self.server_apis["mapbox_server"] = ("mbx", api)
        elif self.server_name == "web_search":
            api = make_error_injected_web_search(BraveSearchAPI(), ExaSearchAPI())
            api.api._load_scenario({})
            self.server_apis["brave_search_server"] = ("brv", api)
            self.server_apis["exa_search_server"] = ("exa", api)

    def _mount_server(self):
        """Initialize the mounting system (no server mounted yet)."""
        self._init_servers()
        self.active_api = self 

    

    def mcp_list_servers(self) -> dict:
        """List all available MCP servers. Use mcp_mount to connect to one."""
        servers = []
        for server_id, info in self.server_catalog.items():
            servers.append({
                "server_id": server_id,
                "name": info["display_name"],
                "description": info["brief"],
            })
        return {
            "available_servers": servers,
            "currently_mounted": self.mounted_server_id,
            "hint": "Use mcp_mount(server_id) to connect and see available tools.",
        }

    def mcp_mount(self, server_id: str) -> dict:
        """Mount an MCP server to access its tools."""
        if server_id not in self.server_catalog:
            return {"error": f"Unknown server: {server_id}"}

        if server_id not in self.server_apis:
            return {
                "error": (
                    f"Server '{server_id}' exists but is not configured for this scenario "
                    f"('{self.scenario_name}')."
                )
            }

        if self.mounted_server_id is not None:
            return {"error": f"Already mounted to '{self.mounted_server_id}'. Use mcp_unmount() first."}

        self.mounted_server_id = server_id
        self.mounted_tools = {}
        self.mounted_alias_to_real = {}
        self.mounted_real_to_alias = {}

        entry = self.server_apis[server_id]
        real_tools = {}

        if isinstance(entry, tuple):
            prefix, api = entry
            for name in dir(api):
                if name.startswith("_"):
                    continue
                if name.startswith(prefix + "_"):
                    attr = getattr(api, name)
                    if callable(attr):
                        real_tools[name] = attr
        else:
            api = entry
            for name in dir(api):
                if name.startswith("_"):
                    continue
                attr = getattr(api, name)
                if callable(attr):
                    real_tools[name] = attr

        alias_counts = {}
        for real_name, method in real_tools.items():
            base_alias = self._get_tool_alias(real_name)
            alias_index = alias_counts.get(base_alias, 0) + 1
            alias_counts[base_alias] = alias_index
            alias = base_alias if alias_index == 1 else f"{base_alias}_alt{alias_index}"
            self.mounted_tools[alias] = method
            self.mounted_alias_to_real[alias] = real_name
            self.mounted_real_to_alias[real_name] = alias

        tool_list = []
        for exposed_name, method in self.mounted_tools.items():
            description = self._sanitize_tool_doc(method.__doc__ or "")
            tool_list.append({"name": exposed_name, "description": description[:80]})

        return {
            "status": "mounted",
            "server_id": server_id,
            "server_name": self.server_catalog[server_id]["display_name"],
            "tools": tool_list,
            "tool_count": len(tool_list),
        }

    def mcp_unmount(self) -> dict:
        """Unmount the current server to switch to another."""
        if self.mounted_server_id is None:
            return {"error": "No server is mounted."}

        old = self.mounted_server_id
        self.mounted_server_id = None
        self.mounted_tools = {}
        self.mounted_alias_to_real = {}
        self.mounted_real_to_alias = {}
        self._invalidate_all_transient_handles()

        return {
            "status": "unmounted",
            "previous_server": old,
            "hint": "Use mcp_list_servers() to see options, then mcp_mount(server_id).",
        }

   

    def _get_tool_alias(self, real_name: str) -> str:
        if real_name in CANONICAL_TOOL_ALIASES:
            return CANONICAL_TOOL_ALIASES[real_name]

        no_prefix = real_name
        if "_" in real_name:
            no_prefix = real_name.split("_", 1)[1]
        digest = hashlib.sha1(real_name.encode("utf-8")).hexdigest()[:6]
        return f"{no_prefix}_{digest}"

    def _sanitize_tool_doc(self, doc: str) -> str:
        replacements = [
            "GitHub", "GitLab", "Slack", "Discord",
            "UberEats", "DoorDash", "Google Maps", "Mapbox",
            "Brave", "Exa",
        ]
        clean = doc
        for token in replacements:
            clean = clean.replace(token, "service")
        return " ".join(clean.split())

    def _invalidate_object_handles(self, obj: Any, visited: Set[int]) -> None:
        if obj is None:
            return
        obj_id = id(obj)
        if obj_id in visited:
            return
        visited.add(obj_id)

        invalidate_fn = getattr(obj, "invalidate_transient_handles", None)
        if callable(invalidate_fn):
            try:
                invalidate_fn()
            except Exception:
                pass

        for child_attr in ("api", "api_a", "api_b"):
            child = getattr(obj, child_attr, None)
            if child is not None:
                self._invalidate_object_handles(child, visited)

    def _invalidate_all_transient_handles(self) -> None:
        visited: Set[int] = set()
        for entry in self.server_apis.values():
            api_obj = entry[1] if isinstance(entry, tuple) else entry
            self._invalidate_object_handles(api_obj, visited)

    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if self.verbose:
            self._log("MODEL -> TOOL CALL", {"tool": tool_name, "args": args})

        resolved_tool_name = tool_name
        if tool_name == "mcp_list_servers":
            result = self.mcp_list_servers()
        elif tool_name == "mcp_mount":
            result = self.mcp_mount(args.get("server_id", ""))
            self._invalidate_all_transient_handles()
            if isinstance(result, dict) and "error" in result:
                err = str(result["error"]).lower()
                if "not configured for this scenario" in err:
                    self.mount_miss_count += 1
                    if self.mount_miss_count > self.max_mount_misses:
                        self.disqualified = True
                        self.disqualify_reason = "Excessive blind server mounting detected"
        elif tool_name == "mcp_unmount":
            result = self.mcp_unmount()
        else:
            if self.mounted_server_id is None:
                result = {"error": "No MCP server mounted. Use mcp_list_servers() and mcp_mount(server_id) first."}
            elif tool_name not in self.mounted_tools:
                result = {"error": f"Tool '{tool_name}' not found. Available tools: {list(self.mounted_tools.keys())[:5]}..."}
            else:
                resolved_tool_name = self.mounted_alias_to_real.get(tool_name, tool_name)
                fn = self.mounted_tools[tool_name]

                try:
                    coerced_args = coerce_args(fn, args)
                except (ValueError, TypeError) as e:
                    result = {"error": f"Parameter type error: {str(e)}"}
                else:
                    sig = inspect.signature(fn)
                    missing = []
                    for param_name, param in sig.parameters.items():
                        if param.default is inspect.Parameter.empty and param_name not in coerced_args:
                            missing.append(param_name)
                    if missing:
                        result = {"error": f"Missing required arguments: {', '.join(missing)}"}
                    else:
                        try:
                            result = fn(**coerced_args)
                        except TypeError as e:
                            result = {"error": f"Tool call failed: {str(e)}"}
                        except Exception as e:
                            result = {"error": f"Unexpected error: {str(e)}"}

        if self.verbose:
            self._log("TOOL -> RESULT", result)

        if (resolved_tool_name in REFRESH_TOOLS and isinstance(result, dict) and "error" not in result):
            self.requires_fresh_resolution = False

        if (isinstance(result, dict) and "error" in result and isinstance(result["error"], str)
                and "stale" in result["error"].lower()):
            self.requires_fresh_resolution = True

        if resolved_tool_name in DECOY_TOOLS:
            self.decoy_calls += 1
            estimated_cost = 0.75
            if isinstance(result, dict):
                cost_value = result.get("estimated_cost_usd")
                if isinstance(cost_value, (int, float)):
                    estimated_cost = float(cost_value)
            self.decoy_cost_usd += estimated_cost
            if self.decoy_calls > self.max_decoy_calls or self.decoy_cost_usd > self.max_decoy_cost_usd:
                self.disqualified = True
                self.disqualify_reason = (
                    "Exceeded decoy budget: costly non-productive tool usage detected"
                )

        if self._is_injected_error(result):
            attempts = self.failing_tool_attempts.get(resolved_tool_name, 0) + 1
            self.failing_tool_attempts[resolved_tool_name] = attempts
            self.injected_error_count += 1
            self.requires_fresh_resolution = True
            self._invalidate_all_transient_handles()

            if attempts > self.max_retries_per_failing_tool:
                result = {
                    "error": {
                        "code": "E_RETRY_LIMIT_EXCEEDED",
                        "message": (
                            f"Retry limit exceeded for '{tool_name}'. "
                            "Switch server/tool instead of retrying the same failing call."
                        ),
                        "retry_after": None,
                    }
                }
                self.disqualified = True
                self.disqualify_reason = "Retry spam detected on failing tool"

            if self.injected_error_count > 6:
                self.disqualified = True
                self.disqualify_reason = "Excessive injected-error retries without strategic pivot"

        self.trace.append({
            "tool": tool_name,
            "resolved_tool": resolved_tool_name,
            "args": args,
            "result": result,
        })

        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            if isinstance(error_msg, dict):
                if error_msg.get("code") or error_msg.get("type") == "SERVICE_SHUTDOWN":
                    self.hit_error = True

        self._check_success(resolved_tool_name, args, result)

        return result

    def _is_injected_error(self, result: dict) -> bool:
        if not isinstance(result, dict):
            return False
        if "error" not in result:
            return False
        return isinstance(result["error"], dict) and "code" in result["error"]

    def _tool_succeeded(self, record: dict) -> bool:
        return isinstance(record.get("result"), dict) and "error" not in record["result"]

    def _iter_successful_calls(self, tool_name: str) -> List[dict]:
        out = []
        for record in self.trace:
            resolved = record.get("resolved_tool", record.get("tool"))
            if resolved == tool_name and self._tool_succeeded(record):
                out.append(record)
        return out

    def _has_successful_call(self, tool_name: str) -> bool:
        return len(self._iter_successful_calls(tool_name)) > 0

    def _meets_prereqs(self, tool_name: str) -> bool:
        scenario_reqs = WORKFLOW_PREREQS.get(self.scenario_name, {})
        requirement_groups = scenario_reqs.get(tool_name, [])
        for group in requirement_groups:
            if not any(self._has_successful_call(candidate) for candidate in group):
                return False
        return True

    def _validate_argument_continuity(self, tool_name: str, args: dict) -> bool:
        args = args or {}

        if tool_name == "dd_checkout_complete":
            searches = self._iter_successful_calls("dd_merchant_search")
            menus = self._iter_successful_calls("dd_offerings_list")
            if searches:
                valid_ids = set()
                for r in searches[-1]["result"].get("available_restaurants", []):
                    rid = r.get("restaurant_id")
                    if rid is not None:
                        valid_ids.add(rid)
                if valid_ids and args.get("restaurant_id") not in valid_ids:
                    return False
            if menus and isinstance(args.get("items"), list):
                valid_items = set()
                for m in menus[-1]["result"].get("menu_items", []):
                    mid = m.get("id")
                    if mid is not None:
                        valid_items.add(mid)
                for it in args.get("items", []):
                    if it.get("item_id") not in valid_items:
                        return False

        if tool_name == "ue_transaction_submit":
            searches = self._iter_successful_calls("ue_vendor_discover")
            menus = self._iter_successful_calls("ue_catalog_fetch")
            if searches:
                valid_ids = set()
                for r in searches[-1]["result"].get("restaurants", []):
                    rid = r.get("id")
                    if rid is not None:
                        valid_ids.add(rid)
                if valid_ids and args.get("restaurant_id") not in valid_ids:
                    return False
            if menus and isinstance(args.get("item_ids"), list):
                valid_items = set()
                for m in menus[-1]["result"].get("menu", []):
                    mid = m.get("item_id")
                    if mid is not None:
                        valid_items.add(mid)
                for iid in args.get("item_ids", []):
                    if iid not in valid_items:
                        return False

        if tool_name in ("gh_ticket_submit", "gh_repo_duplicate", "gh_changeset_propose"):
            lookups = self._iter_successful_calls("gh_project_lookup")
            if lookups:
                valid_full_names = set()
                for item in lookups[-1]["result"].get("items", []):
                    full_name = item.get("full_name")
                    if full_name:
                        valid_full_names.add(full_name)
                owner = args.get("owner")
                repo = args.get("repo")
                if owner and repo and valid_full_names and f"{owner}/{repo}" not in valid_full_names:
                    return False

        if tool_name in ("gl_workitem_new", "gl_project_fork", "gl_diff_request"):
            lookups = self._iter_successful_calls("gl_namespace_query")
            if lookups:
                valid_project_refs = set()
                for item in lookups[-1]["result"].get("items", []):
                    if item.get("id") is not None:
                        valid_project_refs.add(str(item["id"]))
                    if item.get("path_with_namespace"):
                        valid_project_refs.add(str(item["path_with_namespace"]))
                project_id = args.get("project_id")
                if project_id is not None and valid_project_refs and str(project_id) not in valid_project_refs:
                    return False

        if tool_name == "slk_emoji_attach":
            histories = self._iter_successful_calls("slk_timeline_fetch")
            if histories:
                valid_handles = set()
                for msg in histories[-1]["result"].get("messages", []):
                    handle = msg.get("reaction_handle")
                    if handle:
                        valid_handles.add(handle)
                timestamp = args.get("timestamp")
                if valid_handles and timestamp not in valid_handles:
                    return False

        if tool_name == "dsc_emote_add":
            histories = self._iter_successful_calls("dsc_log_retrieve")
            if histories:
                valid_handles = set()
                for msg in histories[-1]["result"].get("messages", []):
                    handle = msg.get("reaction_handle")
                    if handle:
                        valid_handles.add(handle)
                message_id = args.get("message_id")
                if valid_handles and message_id not in valid_handles:
                    return False

        return True

    def _check_success(self, tool_name: str, args: dict, result: dict):
        if self.scenario_name not in SUCCESS_CRITERIA:
            return

        if not isinstance(result, dict):
            return

        if "error" in result:
            return

        for method_name, required_key in SUCCESS_CRITERIA[self.scenario_name]:
            if tool_name == method_name and required_key in result:
                value = result.get(required_key)
                if value in (None, False, 0, "", [], {}):
                    self.success = False
                    self.failure_reason = (
                        f"Final tool '{tool_name}' returned non-actionable '{required_key}' value"
                    )
                    return
                if self.disqualified:
                    self.success = False
                    self.failure_reason = self.disqualify_reason or "Run disqualified by hardening checks"
                    return
                if self.requires_fresh_resolution:
                    self.success = False
                    self.failure_reason = "Success action used stale context; refresh discovery data first"
                    return
                if not self._meets_prereqs(tool_name):
                    self.success = False
                    self.failure_reason = f"Missing required workflow steps before '{tool_name}'"
                    return
                if not self._validate_argument_continuity(tool_name, args):
                    self.success = False
                    self.failure_reason = f"Argument continuity check failed for '{tool_name}'"
                    return

                if self.hit_error:
                    self.success = True
                    self.switched_service = True
                    self.failure_reason = None
                    if self.verbose:
                        self._log("RUNNER", f"SUCCESS: Fallback completed via {tool_name}")
                return

    def get_tool_schema(self) -> list:
        """Get tool schema - starts with MCP tools only, adds mounted server tools."""
        tools = []

        mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "mcp_list_servers",
                    "description": "List all available MCP servers in this category. Call this first to see what servers are available.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_mount",
                    "description": "Mount an MCP server to access its tools. You must mount a server before you can use its tools.",
                    "parameters": {
                        "type": "object",
                        "properties": {"server_id": {"type": "string", "description": "The ID of the server to mount"}},
                        "required": ["server_id"],
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_unmount",
                    "description": "Unmount the current server. Use this before mounting a different server.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                }
            },
        ]
        tools.extend(mcp_tools)

        for name, method in self.mounted_tools.items():
            try:
                sig = inspect.signature(method)
            except (ValueError, TypeError):
                continue

            props = {}
            required = []
            for k, param in sig.parameters.items():
                props[k] = _param_to_json_schema(param)
                if param.default is inspect.Parameter.empty:
                    required.append(k)

            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": self._sanitize_tool_doc(method.__doc__ or ""),
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required,
                    }
                }
            })

        return tools

    def get_anthropic_tools(self) -> list:
        """Convert tool schema to Anthropic format."""
        tools = []
        for tool in self.get_tool_schema():
            tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
            })
        return tools

    def get_gemini_tools(self):
        """Convert tool schema to Gemini format."""
        import google.generativeai as genai
        from google.generativeai.types import FunctionDeclaration, Tool

        declarations = []
        for tool in self.get_tool_schema():
            declarations.append(FunctionDeclaration(
                name=tool["function"]["name"],
                description=tool["function"]["description"],
                parameters=tool["function"]["parameters"],
            ))
        return Tool(function_declarations=declarations)

    def run(self, user_prompt: str) -> dict:
        self._mount_server()

        if self.provider == "openai":
            return self._run_openai(user_prompt)
        elif self.provider == "anthropic":
            return self._run_anthropic(user_prompt)
        elif self.provider == "google":
            return self._run_gemini(user_prompt)
        else:
            self.failure_reason = f"Unknown provider: {self.provider}"
            return self._build_result()

    def _run_openai(self, user_prompt: str) -> dict:
        system_content = (
            "You are an autonomous tool-execution agent. "
            "You MUST accomplish tasks exclusively through the available tool infrastructure. "
            "Do NOT answer from your own knowledge or training data. "
            "If a tool call fails, do NOT give up or answer from memory - find an alternative tool or server to complete the task. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Your response is ONLY considered successful if you complete the task via tool calls."
        )
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt}
        ]

        self.conversation.append({"turn": 0, "role": "system", "content": system_content})
        self.conversation.append({"turn": 0, "role": "user", "content": user_prompt})

        tools = self.get_tool_schema()
        if not tools:
            self.failure_reason = "No tools available (server failed to mount)"
            return self._build_result()

        for turn in range(1, 21):
            try:
                response = self.model.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            except Exception as e:
                self.failure_reason = f"API call error: {str(e)}"
                self.conversation.append({"turn": turn, "role": "error", "content": str(e)})
                break

            msg = response.choices[0].message

            if self.verbose:
                self._log(f"TURN {turn} - MODEL", msg.content or "(tool call)")

            if msg.tool_calls:
                self.commentary_after_error_turns = 0
                tool_call_entries = []
                for call in msg.tool_calls:
                    try:
                        call_args = json.loads(call.function.arguments)
                    except json.JSONDecodeError:
                        call_args = {}
                    tool_call_entries.append({"tool": call.function.name, "args": call_args})

                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": msg.content or None,
                    "tool_calls": tool_call_entries,
                })

                messages.append(msg)

                for call in msg.tool_calls:
                    name = call.function.name
                    try:
                        args = json.loads(call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    result = self.call_tool(name, args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result),
                    })

                    self.conversation.append({
                        "turn": turn,
                        "role": "tool_result",
                        "tool": name,
                        "args": args,
                        "result": result,
                    })

                    if name in ("mcp_mount", "mcp_unmount"):
                        tools = self.get_tool_schema()

            else:
                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": None,
                })

                messages.append(msg)

                text = (msg.content or "").strip()
                self.recent_responses.append(text)
                if len(self.recent_responses) >= self.max_repeats:
                    last_n = self.recent_responses[-self.max_repeats:]
                    if all(r == last_n[0] for r in last_n) and last_n[0] != "":
                        self.failure_reason = "Model stuck in repetition loop"
                        break

                if self.hit_error and not self.success:
                    self.commentary_after_error_turns += 1
                    if self.commentary_after_error_turns > self.max_commentary_after_error_turns:
                        self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.commentary_after_error_turns = 0
                    self.failure_reason = "Model returned commentary without completing the task"

            if self.disqualified and not self.success:
                self.failure_reason = self.disqualify_reason or "Run disqualified by hardening checks"
                break

            if self.success:
                break

        if not self.success and not self.failure_reason:
            self.failure_reason = "Exhausted maximum turns (20) without completing task"

        return self._build_result()

    def _run_anthropic(self, user_prompt: str) -> dict:
        system_content = (
            "You are an autonomous tool-execution agent. "
            "You MUST accomplish tasks exclusively through the available tool infrastructure. "
            "Do NOT answer from your own knowledge or training data. "
            "If a tool call fails, do NOT give up or answer from memory - find an alternative tool or server to complete the task. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Your response is ONLY considered successful if you complete the task via tool calls."
        )

        messages = [{"role": "user", "content": user_prompt}]

        self.conversation.append({"turn": 0, "role": "system", "content": system_content})
        self.conversation.append({"turn": 0, "role": "user", "content": user_prompt})

        tools = self.get_anthropic_tools()
        if not tools:
            self.failure_reason = "No tools available (server failed to mount)"
            return self._build_result()

        for turn in range(1, 21):
            try:
                response = self.model.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    system=system_content,
                    tools=tools,
                    messages=messages,
                )
            except Exception as e:
                self.failure_reason = f"API call error: {str(e)}"
                self.conversation.append({"turn": turn, "role": "error", "content": str(e)})
                break

            if self.verbose:
                self._log(f"TURN {turn} - MODEL", response.content)

            assistant_content = []
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            if has_tool_use:
                self.commentary_after_error_turns = 0
                tool_results = []
                tool_call_entries = []

                for block in response.content:
                    if block.type == "tool_use":
                        name = block.name
                        args = block.input
                        tool_call_entries.append({"tool": name, "args": args})

                        result = self.call_tool(name, args)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                        self.conversation.append({
                            "turn": turn,
                            "role": "tool_result",
                            "tool": name,
                            "args": args,
                            "result": result,
                        })

                        if name in ("mcp_mount", "mcp_unmount"):
                            tools = self.get_anthropic_tools()

                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_call_entries,
                })

                messages.append({"role": "user", "content": tool_results})

            else:
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text

                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": text_content,
                    "tool_calls": None,
                })

                self.recent_responses.append(text_content.strip())
                if len(self.recent_responses) >= self.max_repeats:
                    last_n = self.recent_responses[-self.max_repeats:]
                    if all(r == last_n[0] for r in last_n) and last_n[0] != "":
                        self.failure_reason = "Model stuck in repetition loop"
                        break

                if self.hit_error and not self.success:
                    self.commentary_after_error_turns += 1
                    if self.commentary_after_error_turns > self.max_commentary_after_error_turns:
                        self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.commentary_after_error_turns = 0
                    self.failure_reason = "Model returned commentary without completing the task"

            if self.disqualified and not self.success:
                self.failure_reason = self.disqualify_reason or "Run disqualified by hardening checks"
                break

            if self.success:
                break

            if response.stop_reason == "end_turn" and not has_tool_use:
                if not (
                    self.hit_error
                    and not self.success
                    and self.commentary_after_error_turns <= self.max_commentary_after_error_turns
                ):
                    break

        if not self.success and not self.failure_reason:
            self.failure_reason = "Exhausted maximum turns (20) without completing task"

        return self._build_result()

    def _run_gemini(self, user_prompt: str) -> dict:
        import google.generativeai as genai

        system_content = (
            "You are an autonomous tool-execution agent. "
            "You MUST accomplish tasks exclusively through the available tool infrastructure. "
            "Do NOT answer from your own knowledge or training data. "
            "If a tool call fails, do NOT give up or answer from memory - find an alternative tool or server to complete the task. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Your response is ONLY considered successful if you complete the task via tool calls."
        )

        self.conversation.append({"turn": 0, "role": "system", "content": system_content})
        self.conversation.append({"turn": 0, "role": "user", "content": user_prompt})

        tools = self.get_gemini_tools()

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_content,
                tools=[tools],
            )
            chat = model.start_chat()
        except Exception as e:
            self.failure_reason = f"Failed to initialize Gemini model: {str(e)}"
            return self._build_result()

        current_message = user_prompt

        for turn in range(1, 21):
            try:
                response = chat.send_message(current_message)
            except Exception as e:
                self.failure_reason = f"API call error: {str(e)}"
                self.conversation.append({"turn": turn, "role": "error", "content": str(e)})
                if not (
                    self.hit_error
                    and not self.success
                    and self.commentary_after_error_turns <= self.max_commentary_after_error_turns
                ):
                    break

            if self.verbose:
                self._log(f"TURN {turn} - MODEL", str(response.candidates[0].content))

            candidate = response.candidates[0]
            has_function_call = False
            function_responses = []
            tool_call_entries = []

            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    name = fc.name
                    args = dict(fc.args) if fc.args else {}

                    tool_call_entries.append({"tool": name, "args": args})
                    result = self.call_tool(name, args)

                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=name,
                                response={"result": result}
                            )
                        )
                    )

                    self.conversation.append({
                        "turn": turn,
                        "role": "tool_result",
                        "tool": name,
                        "args": args,
                        "result": result,
                    })

            if has_function_call:
                self.commentary_after_error_turns = 0
                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_call_entries,
                })
                current_message = function_responses
            else:
                text_content = ""
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text

                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": text_content,
                    "tool_calls": None,
                })

                self.recent_responses.append(text_content.strip())
                if len(self.recent_responses) >= self.max_repeats:
                    last_n = self.recent_responses[-self.max_repeats:]
                    if all(r == last_n[0] for r in last_n) and last_n[0] != "":
                        self.failure_reason = "Model stuck in repetition loop"
                        break

                if self.hit_error and not self.success:
                    self.commentary_after_error_turns += 1
                    if self.commentary_after_error_turns > self.max_commentary_after_error_turns:
                        self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.commentary_after_error_turns = 0
                    self.failure_reason = "Model returned commentary without completing the task"
                if not (
                    self.hit_error
                    and not self.success
                    and self.commentary_after_error_turns <= self.max_commentary_after_error_turns
                ):
                    break

            if self.disqualified and not self.success:
                self.failure_reason = self.disqualify_reason or "Run disqualified by hardening checks"
                break

            if self.success:
                break

        if not self.success and not self.failure_reason:
            self.failure_reason = "Exhausted maximum turns (20) without completing task"

        return self._build_result()

    def _build_result(self) -> dict:
        return {
            "success": self.success,
            "hit_error": self.hit_error,
            "switched_service": self.switched_service,
            "failure_reason": self.failure_reason,
            "trace": self.trace,
            "conversation": self.conversation,
        }

    def _log(self, label: str, data: Any):
        print(f"\n[{label}]")
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, default=str))
        else:
            print(data)


class BenchmarkSuite:
    """
    Runs the full benchmark across all scenarios and difficulty levels.
    Supports OpenAI, Anthropic (Claude), and Google (Gemini).
    """

    def __init__(self, model_client, model_name: str, provider: str = "openai", scenarios: list = None, verbose: bool = False, trace_dir: str = None):
        self.model = model_client
        self.model_name = model_name
        self.provider = provider

        self.scenarios = scenarios or list(SCENARIO_TO_SERVER.keys())
        self.verbose = verbose
        self.trace_dir = trace_dir
        self.results = []

        if self.trace_dir:
            os.makedirs(self.trace_dir, exist_ok=True)

    def load_prompts(self) -> dict:
        with open(PROMPTS_FILE, "r") as f:
            return json.load(f)

    def run_all(self):
        prompts = self.load_prompts()
        difficulty_levels = ["easy", "medium", "hard"]
        total = len(self.scenarios) * len(difficulty_levels)
        current = 0

        print("=" * 70)
        print(f"  BENCHMARK: {self.model_name} ({self.provider})")
        print(f"  Scenarios: {len(self.scenarios)} | Levels: {len(difficulty_levels)} | Total runs: {total}")
        print("=" * 70)

        for scenario_name in self.scenarios:
            if scenario_name not in prompts:
                print(f"\n[SKIP] No prompts found for '{scenario_name}'")
                continue

            server_name = SCENARIO_TO_SERVER.get(scenario_name)
            if not server_name or server_name not in MCP_REGISTRY:
                print(f"\n[SKIP] No MCP registry entry for scenario '{scenario_name}'")
                continue

            for level in difficulty_levels:
                current += 1
                prompt = prompts[scenario_name].get(level)
                if not prompt:
                    print(f"\n[SKIP] No {level} prompt for '{scenario_name}'")
                    continue

                print(f"\n{'─' * 70}")
                print(f"  [{current}/{total}] {scenario_name} | {level.upper()}")
                print(f"{'─' * 70}")
                if self.verbose:
                    print(f"  Prompt: {prompt[:80]}...")

                runner = MCPRunner(
                    model_client=self.model,
                    model_name=self.model_name,
                    server_name=server_name,
                    provider=self.provider,
                    level=level,
                    verbose=self.verbose,
                    scenario_name=scenario_name,
                )

                try:
                    result = runner.run(prompt)
                except Exception as e:
                    result = {
                        "success": False,
                        "hit_error": False,
                        "switched_service": False,
                        "failure_reason": f"Runner crashed: {str(e)}",
                        "trace": [],
                    }

                result["scenario"] = scenario_name
                result["server"] = server_name
                result["level"] = level
                result["prompt"] = prompt
                self.results.append(result)

                if self.trace_dir:
                    self._save_trace(scenario_name, level, result)

                status = "PASS" if result["success"] else "FAIL"
                reason = f" ({result['failure_reason']})" if not result["success"] else ""
                print(f"  Result: {status}{reason}")

        self._print_scorecard()

    def _save_trace(self, scenario_name: str, level: str, result: dict):
        filename = f"{scenario_name}_{level}.json"
        filepath = os.path.join(self.trace_dir, filename)
        trace_data = {
            "scenario": scenario_name,
            "server": result.get("server", ""),
            "level": level,
            "model": self.model_name,
            "provider": self.provider,
            "prompt": result.get("prompt", ""),
            "success": result["success"],
            "hit_error": result["hit_error"],
            "switched_service": result["switched_service"],
            "failure_reason": result.get("failure_reason"),
            "conversation": result.get("conversation", []),
            "trace": result.get("trace", []),
        }
        with open(filepath, "w") as f:
            json.dump(trace_data, f, indent=2, default=str)
        print(f"  Trace saved: {filepath}")

    def _print_scorecard(self):
        print("\n")
        print("=" * 70)
        print(f"  SCORECARD - {self.model_name} ({self.provider})")
        print("=" * 70)

        level_stats = {"hard": {"pass": 0, "total": 0}, "medium": {"pass": 0, "total": 0}, "easy": {"pass": 0, "total": 0}}
        server_stats = {}

        for r in self.results:
            level = r["level"]
            server = r["server"]

            level_stats[level]["total"] += 1
            if r["success"]:
                level_stats[level]["pass"] += 1

            if server not in server_stats:
                server_stats[server] = {"pass": 0, "total": 0}
            server_stats[server]["total"] += 1
            if r["success"]:
                server_stats[server]["pass"] += 1

        print("\n  BY DIFFICULTY LEVEL:")
        print(f"  {'Level':<12} {'Pass':>6} {'Total':>6} {'Accuracy':>10}")
        print(f"  {'─' * 36}")
        all_pass = 0
        all_total = 0
        for level in ["easy", "medium", "hard"]:
            p = level_stats[level]["pass"]
            t = level_stats[level]["total"]
            pct = (p / t * 100) if t > 0 else 0
            print(f"  {level.upper():<12} {p:>6} {t:>6} {pct:>9.1f}%")
            all_pass += p
            all_total += t

        avg_pct = (all_pass / all_total * 100) if all_total > 0 else 0
        print(f"  {'─' * 36}")
        print(f"  {'AVERAGE':<12} {all_pass:>6} {all_total:>6} {avg_pct:>9.1f}%")

        print("\n  BY SERVER PAIR:")
        print(f"  {'Server':<20} {'Pass':>6} {'Total':>6} {'Accuracy':>10}")
        print(f"  {'─' * 44}")
        for server in sorted(server_stats.keys()):
            p = server_stats[server]["pass"]
            t = server_stats[server]["total"]
            pct = (p / t * 100) if t > 0 else 0
            print(f"  {server:<20} {p:>6} {t:>6} {pct:>9.1f}%")

        print("\n  DETAILED RESULTS:")
        print(f"  {'Scenario':<30} {'Level':<8} {'Result':<8} {'Reason'}")
        print(f"  {'─' * 80}")
        for r in self.results:
            status = "PASS" if r["success"] else "FAIL"
            reason = r.get("failure_reason", "") or "" if not r["success"] else ""
            if len(reason) > 30:
                reason = reason[:30] + "..."
            scenario = r.get('scenario', r.get('server', 'unknown'))
            print(f"  {scenario:<30} {r['level']:<8} {status:<8} {reason}")

        print("\n" + "=" * 70)
        print(f"  FINAL SCORE: {all_pass}/{all_total} ({avg_pct:.1f}%)")
        print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Fallback Benchmark Runner")
    parser.add_argument("--provider", type=str, default="openai", choices=["openai", "anthropic", "google"],
                        help="API provider to use (openai, anthropic, google)")
    parser.add_argument("--model", type=str, default=None,
                        help="Model to test (default: provider's default model)")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Run only a specific scenario (e.g., code_hosting_create_issue)")
    parser.add_argument("--server", type=str, default=None,
                        help="Run only scenarios for a specific server pair (e.g., code_hosting)")
    parser.add_argument("--level", type=str, default=None, choices=["easy", "medium", "hard"],
                        help="Run only a specific difficulty level")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full tool call traces in console")
    parser.add_argument("--trace", type=str, default=None, metavar="DIR",
                        help="Save full conversation traces to DIR as JSON files (e.g., --trace ./traces)")

    args = parser.parse_args()

    model_name = args.model or DEFAULT_MODELS[args.provider]
    client = create_client(args.provider)

    if args.scenario:
        scenarios = [args.scenario]
    elif args.server:
        scenarios = [s for s, srv in SCENARIO_TO_SERVER.items() if srv == args.server]
    else:
        scenarios = list(SCENARIO_TO_SERVER.keys())

    suite = BenchmarkSuite(
        model_client=client,
        model_name=model_name,
        provider=args.provider,
        scenarios=scenarios,
        verbose=args.verbose,
        trace_dir=args.trace,
    )

    if args.level:
        prompts = suite.load_prompts()
        total = len(scenarios)
        current = 0

        print("=" * 70)
        print(f"  BENCHMARK: {model_name} ({args.provider}) | Level: {args.level.upper()}")
        print(f"  Scenarios: {len(scenarios)} | Total runs: {total}")
        print("=" * 70)

        for scenario_name in scenarios:
            current += 1
            if scenario_name not in prompts:
                print(f"\n[SKIP] {scenario_name}")
                continue

            server_name = SCENARIO_TO_SERVER.get(scenario_name)
            if not server_name or server_name not in MCP_REGISTRY:
                print(f"\n[SKIP] {scenario_name} (no server)")
                continue

            prompt = prompts[scenario_name].get(args.level)
            if not prompt:
                continue

            print(f"\n{'─' * 70}")
            print(f"  [{current}/{total}] {scenario_name} | {args.level.upper()}")
            print(f"{'─' * 70}")

            runner = MCPRunner(
                model_client=client,
                model_name=model_name,
                server_name=server_name,
                provider=args.provider,
                level=args.level,
                verbose=args.verbose,
                scenario_name=scenario_name,
            )

            try:
                result = runner.run(prompt)
            except Exception as e:
                result = {
                    "success": False,
                    "hit_error": False,
                    "switched_service": False,
                    "failure_reason": f"Runner crashed: {str(e)}",
                    "trace": [],
                }

            result["scenario"] = scenario_name
            result["server"] = server_name
            result["level"] = args.level
            result["prompt"] = prompt
            suite.results.append(result)

            if suite.trace_dir:
                suite._save_trace(scenario_name, args.level, result)

            status = "PASS" if result["success"] else "FAIL"
            reason = f" ({result['failure_reason']})" if not result["success"] else ""
            print(f"  Result: {status}{reason}")

        suite._print_scorecard()
    else:
        suite.run_all()
