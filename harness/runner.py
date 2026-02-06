import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import inspect
import json
import time
from typing import Dict, Any, List, get_type_hints

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
    make_error_injected_food_delivery,
    make_error_injected_code_hosting,
    make_error_injected_web_search,
    make_error_injected_team_messaging,
    make_error_injected_maps,
)


PROMPTS_FILE = os.path.join(PROJECT_ROOT, "scenarios", "prompts.json")

DEFAULT_MODELS = {
    "openai": "gpt-5.2",
    "anthropic": "claude-sonnet-4-5-20250929",
    "google": "gemini-3.0-flash",
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
    "team_messaging_dm": "team_messaging",
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
    "food_delivery":    [
        ("ubereats_place_order", "order_id"), ("doordash_submit_order", "confirmation_number"),
        ("ubereats_get_order_status", "status"), ("doordash_check_order_status", "order_status"),
    ],
    "code_hosting":     [
        ("github_create_issue", "number"), ("gitlab_create_issue", "iid"),
        ("github_create_pull_request", "number"), ("gitlab_create_merge_request", "iid"),
        ("github_search_repositories", "total_count"), ("gitlab_search_repositories", "total_count"),
        ("github_fork_repository", "full_name"), ("gitlab_fork_repository", "id"),
    ],
    "web_search":       [
        ("brave_brave_web_search", "results"), ("exa_web_search_exa", "results"),
        ("exa_get_code_context_exa", "results"), ("exa_company_research_exa", "found"),
    ],
    "team_messaging":   [
        ("slack_slack_post_message", "ts"), ("discord_send_message", "message"),
        ("slack_slack_add_reaction", "ok"), ("discord_add_reaction", "success"),
        ("discord_send_private_message", "message"),
    ],
    "maps":             [
        ("google_maps_directions", "routes"), ("mapbox_mapbox_directions", "routes"),
        ("google_maps_geocode", "results"), ("mapbox_mapbox_geocode", "features"),
        ("google_maps_search_places", "results"), ("mapbox_mapbox_search_places", "features"),
    ],
}


def create_client(provider: str):
    """Create an API client for the specified provider."""
    if provider == "openai":
        from openai import OpenAI
        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    elif provider == "anthropic":
        import anthropic
        return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    elif provider == "google":
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
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
    """

    def __init__(self, model_client, model_name: str, server_name: str, provider: str = "openai", level: str = "easy", verbose: bool = True):
        self.model = model_client
        self.model_name = model_name
        self.server_name = server_name
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

    def _mount_server(self):
        self.active_api = MCP_REGISTRY[self.server_name]()
        self.active_api.api._load_scenario({})

    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if self.verbose:
            self._log("MODEL -> TOOL CALL", {"tool": tool_name, "args": args})

        if self.active_api is None:
            return {"error": "No MCP server mounted"}

        if not hasattr(self.active_api, tool_name):
            return {"error": f"Tool '{tool_name}' not found in server '{self.server_name}'"}

        fn = getattr(self.active_api, tool_name)

        try:
            coerced_args = coerce_args(fn, args)
        except (ValueError, TypeError) as e:
            return {"error": f"Parameter type error: {str(e)}"}

        sig = inspect.signature(fn)
        missing = []
        for param_name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty and param_name not in coerced_args:
                missing.append(param_name)
        if missing:
            return {"error": f"Missing required arguments: {', '.join(missing)}"}

        try:
            result = fn(**coerced_args)
        except TypeError as e:
            return {"error": f"Tool call failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

        if self.verbose:
            self._log("TOOL -> RESULT", result)

        self.trace.append({
            "tool": tool_name,
            "args": coerced_args,
            "result": result,
        })

        if isinstance(result, dict) and "error" in result:
            error_msg = result["error"]
            if isinstance(error_msg, dict) and error_msg.get("type") == "SERVICE_SHUTDOWN":
                self.hit_error = True

        self._check_success(tool_name, result)

        return result

    def _check_success(self, tool_name: str, result: dict):
        if self.server_name not in SUCCESS_CRITERIA:
            return

        if not isinstance(result, dict):
            return

        if "error" in result:
            return

        for method_name, required_key in SUCCESS_CRITERIA[self.server_name]:
            if tool_name == method_name and required_key in result:
                if self.hit_error:
                    self.success = True
                    self.switched_service = True
                    if self.verbose:
                        self._log("RUNNER", f"SUCCESS: Fallback completed via {tool_name}")
                return

    def get_tool_schema(self) -> list:
        tools = []

        if self.active_api is None:
            return tools

        for name in dir(self.active_api):
            if name.startswith("_"):
                continue
            attr = getattr(self.active_api, name)
            if not callable(attr):
                continue

            try:
                sig = inspect.signature(attr)
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
                    "description": attr.__doc__ or "",
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
            "You are an autonomous tool-using agent. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Try your best to use the available tools to complete the task."
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

            else:
                self.conversation.append({
                    "turn": turn,
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": None,
                })

                messages.append(msg)

                if self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary without completing the task"

            if self.success:
                break

        if not self.success and not self.failure_reason:
            self.failure_reason = "Exhausted maximum turns (20) without completing task"

        return self._build_result()

    def _run_anthropic(self, user_prompt: str) -> dict:
        system_content = (
            "You are an autonomous tool-using agent. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Try your best to use the available tools to complete the task."
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

                if self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary without completing the task"

            if self.success:
                break

            if response.stop_reason == "end_turn" and not has_tool_use:
                break

        if not self.success and not self.failure_reason:
            self.failure_reason = "Exhausted maximum turns (20) without completing task"

        return self._build_result()

    def _run_gemini(self, user_prompt: str) -> dict:
        import google.generativeai as genai

        system_content = (
            "You are an autonomous tool-using agent. "
            "You may NOT ask the user follow-up questions. "
            "You must make reasonable assumptions and complete the task. "
            "If required information is missing, choose sensible defaults. "
            "If you are told to login just put default login info to properly login. "
            "Try your best to use the available tools to complete the task."
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

                if self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary instead of switching services"
                elif not self.hit_error and not self.success:
                    self.failure_reason = "Model returned commentary without completing the task"
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
            reason = r.get("failure_reason", "") or ""
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
