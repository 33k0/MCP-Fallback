# MCP Fallback Benchmark

A benchmark suite for evaluating AI agents' ability to recover from tool failures by switching to equivalent alternative services. Built for Berkeley Sky Labs.

## Overview

This benchmark tests whether language models can autonomously handle service failures when using MCP (Model Context Protocol) tools. When one service fails, can the model recognize the failure and switch to an equivalent alternative service to complete the task?

### Core Mechanism

1. The model receives a task (e.g., "Send a message to the general channel")
2. It has access to tools from TWO equivalent services (e.g., Slack + Discord)
3. Whichever service it tries FIRST will fail with a "SERVICE_SHUTDOWN" error
4. Success = the model recognizes the failure and completes the task using the OTHER service
5. Failure = the model gives up, loops, or returns commentary instead of switching

## Project Structure

```
SkyLabsProjectPreliminaries/
├── harness/
│   └── runner.py              # Main benchmark runner (supports OpenAI, Anthropic, Google)
├── mock_servers/
│   ├── food_delivery_api.py   # UberEats + DoorDash (legacy paired server)
│   ├── github_api.py          # GitHub MCP mock (20 tools)
│   ├── gitlab_api.py          # GitLab MCP mock (9 tools)
│   ├── brave_search_api.py    # Brave Search mock (2 tools)
│   ├── exa_search_api.py      # Exa Search mock (9 tools)
│   ├── slack_api.py           # Slack MCP mock (8 tools)
│   ├── discord_api.py         # Discord MCP mock (10 tools)
│   ├── google_maps_api.py     # Google Maps mock (7 tools)
│   └── mapbox_api.py          # Mapbox mock (10 tools)
├── error_injection/
│   └── controller.py          # Error injection + server pairing logic
├── scenarios/
│   └── prompts.json           # 15 unique test scenarios (easy/medium/hard)
├── traces/                    # Output directory for conversation traces
└── README.md
```

## Supported Providers & Models

The benchmark supports three AI providers:

| Provider | Default Model | Environment Variable |
|----------|---------------|---------------------|
| **OpenAI** | `gpt-5.2` | `OPENAI_API_KEY` |
| **Anthropic** | `claude-sonnet-4-5-20250929` | `ANTHROPIC_API_KEY` |
| **Google** | `gemini-3.0-flash` | `GOOGLE_API_KEY` |

## Server Pairs & Why They Were Chosen

Each server pair was selected based on real MCP server schemas from the official [Model Context Protocol servers repository](https://github.com/modelcontextprotocol/servers).

### 1. Food Delivery: UberEats + DoorDash
**Purpose:** Legacy baseline pair with symmetric tool sets.

| UberEats | DoorDash |
|----------|----------|
| `ubereats_login` | `doordash_authenticate` |
| `ubereats_search_restaurants` | `doordash_find_restaurants` |
| `ubereats_get_menu` | `doordash_view_menu` |
| `ubereats_place_order` | `doordash_submit_order` |
| `ubereats_get_order_status` | `doordash_check_order_status` |

**What it tests:** Pure fallback - both services have identical capabilities. Can the model find the equivalent method on the other service?

---

### 2. Code Hosting: GitHub + GitLab
**Purpose:** Real-world MCP servers with asymmetric tool counts.

| GitHub (20 tools) | GitLab (9 tools) |
|-------------------|------------------|
| Full repo management | Core repo operations |
| Issues, PRs, branches | Issues, MRs, branches |
| Code/issue/user search | Repository search only |
| Fork, merge, comments | Basic operations |

**What it tests:**
- Fallback when target service has FEWER tools
- Model must adapt when some GitHub features don't exist on GitLab
- Tests scenarios: create issue, fork repo, create PR, search repos

---

### 3. Web Search: Brave + Exa
**Purpose:** Minimal vs feature-rich search APIs.

| Brave (2 tools) | Exa (9 tools) |
|-----------------|---------------|
| `brave_web_search` | `web_search_exa` |
| `brave_local_search` | `get_code_context_exa` |
| | `company_research_exa` |
| | `deep_search_exa` |
| | `people_search_exa` |
| | ...and more |

**What it tests:**
- Fallback when target service has MORE tools
- Model must discover Exa's specialized tools (code search, company research)
- Tests scenarios: general search, code examples, company research

---

### 4. Team Messaging: Slack + Discord
**Purpose:** Similar services with unique capabilities on each side.

| Slack (8 tools) | Discord (10 tools) |
|-----------------|-------------------|
| `slack_post_message` | `send_message` |
| `slack_list_channels` | `list_channels` |
| `slack_add_reaction` | `add_reaction` |
| `slack_get_channel_history` | `read_messages` |
| `slack_reply_to_thread` | — |
| — | `edit_message` |
| — | `delete_message` |
| — | `send_private_message` |

**What it tests:**
- Asymmetric features (Discord can edit/delete/DM, Slack has threads)
- Model must recognize when a feature doesn't exist on the fallback service
- Tests scenarios: send message, add reaction, send DM

---

### 5. Maps & Navigation: Google Maps + Mapbox
**Purpose:** Standard mapping vs geospatial computation.

| Google Maps (7 tools) | Mapbox (10 tools) |
|-----------------------|-------------------|
| `maps_geocode` | `mapbox_geocode` |
| `maps_directions` | `mapbox_directions` |
| `maps_search_places` | `mapbox_search_places` |
| `maps_distance_matrix` | `mapbox_matrix` |
| `maps_elevation` | — |
| — | `mapbox_bearing` |
| — | `mapbox_isochrone` |
| — | `mapbox_distance` (offline) |

**What it tests:**
- Both services have equivalent core tools (directions, geocode, places)
- Tests scenarios: directions, geocode, place search

## Difficulty Levels

Each scenario has three difficulty levels:

| Level | Description | Example Prompt |
|-------|-------------|----------------|
| **Easy** | Explicitly names both services + hints to switch | "Send a message to general. Use Slack or Discord. If one fails, switch to the other." |
| **Medium** | Names both services, no switching hint | "Send a message to general. Use Slack or Discord." |
| **Hard** | Generic task, no service hints | "Send a message to general." |

## The 15 Test Scenarios

| Category | Scenario | Tests |
|----------|----------|-------|
| Food Delivery | `food_delivery_order` | Place an order |
| | `food_delivery_status` | Check order status (order ID 1001) |
| Code Hosting | `code_hosting_create_issue` | Create a bug report |
| | `code_hosting_fork_repo` | Fork a repository |
| | `code_hosting_create_pr` | Create pull/merge request |
| | `code_hosting_search_repos` | Search repositories |
| Web Search | `web_search_general` | General web search |
| | `web_search_code` | Find code examples |
| | `web_search_company` | Company research |
| Team Messaging | `team_messaging_send` | Send channel message |
| | `team_messaging_react` | Add reaction to a message |
| | `team_messaging_dm` | Send direct message |
| Maps | `maps_directions` | Get driving directions |
| | `maps_geocode` | Get lat/lng coordinates |
| | `maps_places` | Search for nearby places |

## Running the Benchmark

### Prerequisites

```bash
pip install openai anthropic google-generativeai
```

Set your API key for the provider you want to use:
```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# For Google (Gemini)
export GOOGLE_API_KEY="AIza..."
```

### Basic Usage

Run the full benchmark with OpenAI (default):
```bash
python harness/runner.py
```

Run with Anthropic Claude:
```bash
python harness/runner.py --provider anthropic
```

Run with Google Gemini:
```bash
python harness/runner.py --provider google
```

### Options

```bash
# Test a specific model
python harness/runner.py --provider openai --model gpt-4o
python harness/runner.py --provider anthropic --model claude-opus-4-20250514
python harness/runner.py --provider google --model gemini-2.0-pro

# Run only one scenario
python harness/runner.py --scenario code_hosting_create_issue

# Run all scenarios for one server pair
python harness/runner.py --server maps

# Run only hard difficulty
python harness/runner.py --level hard

# Show detailed tool call traces
python harness/runner.py --verbose

# Save conversation traces to files
python harness/runner.py --trace ./traces

# Combine options
python harness/runner.py --provider anthropic --server team_messaging --level medium --verbose
```

### Output

The benchmark prints a scorecard showing:
- Pass/fail rate by difficulty level
- Pass/fail rate by server pair
- Detailed results for each scenario

Example output:
```
======================================================================
  SCORECARD - claude-sonnet-4-5-20250929 (anthropic)
======================================================================

  BY DIFFICULTY LEVEL:
  Level           Pass  Total   Accuracy
  ────────────────────────────────────
  EASY               12     15      80.0%
  MEDIUM              9     15      60.0%
  HARD                5     15      33.3%
  ────────────────────────────────────
  AVERAGE            26     45      57.8%

  BY SERVER PAIR:
  Server                Pass  Total   Accuracy
  ────────────────────────────────────────────
  code_hosting            8     12      66.7%
  food_delivery           5      6      83.3%
  maps                    4      9      44.4%
  team_messaging          5      9      55.6%
  web_search              4      9      44.4%
```

## How Success is Measured

A run is marked **PASS** if:
1. The model called a tool from service A (or B)
2. That tool returned a `SERVICE_SHUTDOWN` error
3. The model then called the equivalent tool on service B (or A)
4. That tool returned a successful result with the expected key

A run is marked **FAIL** if:
- Model gives up after the error
- Model returns commentary instead of trying another tool
- Model loops without switching services
- Model crashes or hits 20 turn limit

## Architecture Details

### Error Injection

The `ErrorInjectedAPI` wrapper intercepts tool calls:
```python
# First call to ANY of these methods fails
fail_methods = ["slack_slack_post_message", "discord_send_message"]

# If model calls slack first -> error
# Then discord works fine (and vice versa)
```

Every scenario has guaranteed error injection - all equivalent method pairs are included in the `fail_methods` list.

### Server Pairing

The `PairedServerAPI` class combines two separate APIs:
```python
# GitHub methods become: github_create_issue, github_fork_repository, ...
# GitLab methods become: gitlab_create_issue, gitlab_fork_repository, ...
# Model sees ALL tools from both services
```

### Multi-Provider Support

The runner automatically converts tool schemas to each provider's format:
- **OpenAI**: Uses function calling with `tools` parameter
- **Anthropic**: Converts to Claude's `tool_use` format with `input_schema`
- **Google**: Converts to Gemini's `FunctionDeclaration` format

## Mock Servers

The servers are mocks based on real MCP schemas but return simulated data. They don't make actual API calls to GitHub, Slack, etc.

Pre-existing test data:
- **Food Delivery**: Orders 1001 (UberEats) and 1002 (DoorDash) exist for status checking
- **Code Hosting**: Repository `acme-corp/web-app` exists for issue/PR creation

## Contact

Sri Vatsa
Berkeley Sky Labs
