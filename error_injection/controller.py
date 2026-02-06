# Error Injection Controller - Wraps mock APIs, injects failures on first call
import inspect


class PairedServerAPI:
    """
    Combines TWO separate API instances into one, prefixing method names
    to avoid collisions. This allows the model to see tools from both
    services and choose which one to call.

    Example: GitHub API methods become github_* and GitLab becomes gitlab_*
    """

    def __init__(self, api_a, prefix_a: str, api_b, prefix_b: str):
        """
        Args:
            api_a: First API instance
            prefix_a: Prefix for first API's methods (e.g., "github")
            api_b: Second API instance
            prefix_b: Prefix for second API's methods (e.g., "gitlab")
        """
        self.api_a = api_a
        self.api_b = api_b
        self.prefix_a = prefix_a
        self.prefix_b = prefix_b

        # Bind methods from API A with prefix
        for name, method in inspect.getmembers(api_a, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            prefixed_name = f"{prefix_a}_{name}"
            setattr(self, prefixed_name, method)

        # Bind methods from API B with prefix
        for name, method in inspect.getmembers(api_b, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            prefixed_name = f"{prefix_b}_{name}"
            setattr(self, prefixed_name, method)

    def _load_scenario(self, scenario: dict):
        """Load scenario into both APIs."""
        if hasattr(self.api_a, '_load_scenario'):
            self.api_a._load_scenario(scenario)
        if hasattr(self.api_b, '_load_scenario'):
            self.api_b._load_scenario(scenario)


class ErrorInjectedAPI:
    """
    Generic error injection wrapper. Proxies all calls to the underlying API,
    but intercepts a GROUP of equivalent methods and fails whichever one is
    called FIRST. The second service's equivalent method works normally.

    Example: fail_methods = ["ubereats_place_order", "doordash_submit_order"]
    If the model calls ubereats_place_order first -> error.
    Then doordash_submit_order works fine.
    If the model calls doordash_submit_order first -> error.
    Then ubereats_place_order works fine.
    """

    def __init__(self, api, fail_methods: list, error_responses: dict):
        """
        Args:
            api: The underlying mock API instance.
            fail_methods (list): List of equivalent method names. The FIRST one
                called will fail; all others will work normally after that.
            error_responses (dict): Maps method_name -> error dict to return.
                Each method gets its own realistic error message.
        """
        self.api = api
        self.fail_methods = set(fail_methods)
        self.error_responses = error_responses
        self.first_call_failed = False
        self.failed_method = None

        # Bind ALL public methods from the underlying API onto this wrapper
        # so dir() / inspect can discover them for tool schema generation.
        for name, method in inspect.getmembers(self.api, predicate=inspect.ismethod):
            if name.startswith("_"):
                continue
            if name in self.fail_methods:
                setattr(self, name, self._make_guarded_method(name, method))
            else:
                setattr(self, name, method)

    def _make_guarded_method(self, method_name, original_method):
        """
        Create a wrapper that fails on the FIRST call across the group,
        then passes through for all subsequent calls (including from
        the other service).
        """
        def wrapper(*args, **kwargs):
            if not self.first_call_failed:
                self.first_call_failed = True
                self.failed_method = method_name
                return self.error_responses.get(method_name, {
                    "error": {
                        "type": "SERVICE_SHUTDOWN",
                        "message": f"{method_name} service has been permanently discontinued."
                    }
                })
            return original_method(*args, **kwargs)

        wrapper.__doc__ = original_method.__doc__
        wrapper.__signature__ = inspect.signature(original_method)
        wrapper.__name__ = original_method.__name__
        return wrapper


# =============================================================================
# Factory functions for each MCP server
# =============================================================================

def make_error_injected_food_delivery(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=[
            "ubereats_place_order", "doordash_submit_order",
            "ubereats_get_order_status", "doordash_check_order_status",
        ],
        error_responses={
            "ubereats_place_order": {"error": {"type": "SERVICE_SHUTDOWN", "message": "UberEats ordering service has been permanently discontinued. This endpoint is no longer functional."}},
            "doordash_submit_order": {"error": {"type": "SERVICE_SHUTDOWN", "message": "DoorDash order submission service has been permanently shut down. This endpoint is no longer available."}},
            "ubereats_get_order_status": {"error": {"type": "SERVICE_SHUTDOWN", "message": "UberEats order status service has been permanently discontinued. This endpoint is no longer functional."}},
            "doordash_check_order_status": {"error": {"type": "SERVICE_SHUTDOWN", "message": "DoorDash order status service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_ride_hailing(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["uber_request_ride", "lyft_book_ride"],
        error_responses={
            "uber_request_ride": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Uber ride request service has been permanently discontinued. This endpoint is no longer functional."}},
            "lyft_book_ride": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Lyft ride booking service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_social_posting(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["twitter_post_tweet", "mastodon_create_toot"],
        error_responses={
            "twitter_post_tweet": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Twitter posting service has been permanently discontinued. This endpoint is no longer functional."}},
            "mastodon_create_toot": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Mastodon toot creation service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_email(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["gmail_send_email", "outlook_send_message"],
        error_responses={
            "gmail_send_email": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Gmail send service has been permanently discontinued. This endpoint is no longer functional."}},
            "outlook_send_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Outlook message sending service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_payment(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["venmo_send_payment", "zelle_transfer_money"],
        error_responses={
            "venmo_send_payment": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Venmo payment service has been permanently discontinued. This endpoint is no longer functional."}},
            "zelle_transfer_money": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Zelle transfer service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_music_streaming(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["spotify_play_song", "apple_music_play_track"],
        error_responses={
            "spotify_play_song": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Spotify playback service has been permanently discontinued. This endpoint is no longer functional."}},
            "apple_music_play_track": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Apple Music playback service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_navigation(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["google_maps_get_directions", "mapbox_get_route"],
        error_responses={
            "google_maps_get_directions": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Google Maps directions service has been permanently discontinued. This endpoint is no longer functional."}},
            "mapbox_get_route": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Mapbox routing service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_cloud_storage(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["google_drive_upload_file", "dropbox_upload"],
        error_responses={
            "google_drive_upload_file": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Google Drive upload service has been permanently discontinued. This endpoint is no longer functional."}},
            "dropbox_upload": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Dropbox upload service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_messaging(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["slack_send_message", "teams_post_message"],
        error_responses={
            "slack_send_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Slack messaging service has been permanently discontinued. This endpoint is no longer functional."}},
            "teams_post_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Teams messaging service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_hotel_booking(api):
    return ErrorInjectedAPI(
        api=api,
        fail_methods=["booking_reserve_room", "airbnb_book_stay"],
        error_responses={
            "booking_reserve_room": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Booking.com reservation service has been permanently discontinued. This endpoint is no longer functional."}},
            "airbnb_book_stay": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Airbnb booking service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


# =============================================================================
# NEW: Separate server pair factories (for real MCP-based servers)
# =============================================================================

def make_error_injected_code_hosting(github_api, gitlab_api):
    """
    Combine GitHub and GitLab APIs, with error injection on key methods.
    Fails the first call to any equivalent method pair.
    """
    paired = PairedServerAPI(github_api, "github", gitlab_api, "gitlab")
    return ErrorInjectedAPI(
        api=paired,
        fail_methods=[
            "github_create_issue", "gitlab_create_issue",
            "github_create_pull_request", "gitlab_create_merge_request",
            "github_search_repositories", "gitlab_search_repositories",
            "github_fork_repository", "gitlab_fork_repository",
        ],
        error_responses={
            "github_create_issue": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitHub Issues service has been permanently discontinued. This endpoint is no longer functional."}},
            "gitlab_create_issue": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitLab Issues service has been permanently shut down. This endpoint is no longer available."}},
            "github_create_pull_request": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitHub Pull Requests service has been permanently discontinued. This endpoint is no longer functional."}},
            "gitlab_create_merge_request": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitLab Merge Requests service has been permanently shut down. This endpoint is no longer available."}},
            "github_search_repositories": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitHub Repository Search service has been permanently discontinued. This endpoint is no longer functional."}},
            "gitlab_search_repositories": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitLab Repository Search service has been permanently shut down. This endpoint is no longer available."}},
            "github_fork_repository": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitHub Fork service has been permanently discontinued. This endpoint is no longer functional."}},
            "gitlab_fork_repository": {"error": {"type": "SERVICE_SHUTDOWN", "message": "GitLab Fork service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_web_search(brave_api, exa_api):
    """
    Combine Brave and Exa search APIs, with error injection on search methods.
    All search-related methods are in the fail group.
    """
    paired = PairedServerAPI(brave_api, "brave", exa_api, "exa")
    return ErrorInjectedAPI(
        api=paired,
        fail_methods=[
            "brave_brave_web_search", "exa_web_search_exa",
            "exa_get_code_context_exa", "exa_company_research_exa",
        ],
        error_responses={
            "brave_brave_web_search": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Brave Search service has been permanently discontinued. This endpoint is no longer functional."}},
            "exa_web_search_exa": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Exa Search service has been permanently shut down. This endpoint is no longer available."}},
            "exa_get_code_context_exa": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Exa Code Search service has been permanently shut down. This endpoint is no longer available."}},
            "exa_company_research_exa": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Exa Company Research service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_team_messaging(slack_api, discord_api):
    """
    Combine Slack and Discord APIs, with error injection on messaging methods.
    All messaging-related methods are in the fail group.
    """
    paired = PairedServerAPI(slack_api, "slack", discord_api, "discord")
    return ErrorInjectedAPI(
        api=paired,
        fail_methods=[
            "slack_slack_post_message", "discord_send_message",
            "slack_slack_add_reaction", "discord_add_reaction",
            "discord_send_private_message",
        ],
        error_responses={
            "slack_slack_post_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Slack messaging service has been permanently discontinued. This endpoint is no longer functional."}},
            "discord_send_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Discord messaging service has been permanently shut down. This endpoint is no longer available."}},
            "slack_slack_add_reaction": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Slack reactions service has been permanently discontinued. This endpoint is no longer functional."}},
            "discord_add_reaction": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Discord reactions service has been permanently shut down. This endpoint is no longer available."}},
            "discord_send_private_message": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Discord DM service has been permanently shut down. This endpoint is no longer available."}},
        }
    )


def make_error_injected_maps(google_maps_api, mapbox_api):
    """
    Combine Google Maps and Mapbox APIs, with error injection on map methods.
    All mapping-related methods are in the fail group.
    """
    paired = PairedServerAPI(google_maps_api, "google", mapbox_api, "mapbox")
    return ErrorInjectedAPI(
        api=paired,
        fail_methods=[
            "google_maps_directions", "mapbox_mapbox_directions",
            "google_maps_geocode", "mapbox_mapbox_geocode",
            "google_maps_search_places", "mapbox_mapbox_search_places",
        ],
        error_responses={
            "google_maps_directions": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Google Maps Directions service has been permanently discontinued. This endpoint is no longer functional."}},
            "mapbox_mapbox_directions": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Mapbox Directions service has been permanently shut down. This endpoint is no longer available."}},
            "google_maps_geocode": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Google Maps Geocoding service has been permanently discontinued. This endpoint is no longer functional."}},
            "mapbox_mapbox_geocode": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Mapbox Geocoding service has been permanently shut down. This endpoint is no longer available."}},
            "google_maps_search_places": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Google Maps Places service has been permanently discontinued. This endpoint is no longer functional."}},
            "mapbox_mapbox_search_places": {"error": {"type": "SERVICE_SHUTDOWN", "message": "Mapbox Places service has been permanently shut down. This endpoint is no longer available."}},
        }
    )
