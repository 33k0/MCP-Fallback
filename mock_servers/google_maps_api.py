# Google Maps MCP Server Mock
# Based on real Google Maps MCP server from modelcontextprotocol/servers
#
# Google Maps has 7 tools:
#   1. maps_geocode - Convert address to coordinates
#   2. maps_reverse_geocode - Convert coordinates to address
#   3. maps_search_places - Search for places/POIs
#   4. maps_place_details - Get detailed place information
#   5. maps_distance_matrix - Calculate distances/times between points
#   6. maps_directions - Get route directions
#   7. maps_elevation - Get elevation data
#
# Mapbox has more geospatial tools, so this tests adaptation when
# falling back to a service with different capabilities.

from typing import Dict, Any, Optional, List

DEFAULT_STATE = {
    "places": [
        {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Google Sydney",
            "formatted_address": "48 Pirrama Rd, Pyrmont NSW 2009, Australia",
            "geometry": {"lat": -33.866651, "lng": 151.195827},
            "types": ["point_of_interest", "establishment"],
            "rating": 4.5,
            "user_ratings_total": 1234,
            "opening_hours": {"open_now": True},
        },
        {
            "place_id": "ChIJrTLr-GyuEmsRBfy61i59si0",
            "name": "Sydney Opera House",
            "formatted_address": "Bennelong Point, Sydney NSW 2000, Australia",
            "geometry": {"lat": -33.856784, "lng": 151.215297},
            "types": ["tourist_attraction", "point_of_interest"],
            "rating": 4.7,
            "user_ratings_total": 45678,
            "opening_hours": {"open_now": True},
        },
        {
            "place_id": "ChIJ-c8LpSKuEmsRUHkGGI6kzYk",
            "name": "The Coffee Shop",
            "formatted_address": "123 George St, Sydney NSW 2000, Australia",
            "geometry": {"lat": -33.865143, "lng": 151.209900},
            "types": ["cafe", "food", "point_of_interest"],
            "rating": 4.2,
            "user_ratings_total": 89,
            "opening_hours": {"open_now": True},
        },
        {
            "place_id": "ChIJfake_skylabs_01",
            "name": "SkyLabs Research Center",
            "formatted_address": "1200 Innovation Drive, Boulder, CO 80301, USA",
            "geometry": {"lat": 40.0150, "lng": -105.2705},
            "types": ["point_of_interest", "establishment"],
            "rating": 4.8,
            "user_ratings_total": 42,
            "opening_hours": {"open_now": True},
        },
        {
            "place_id": "ChIJfake_neutron_02",
            "name": "Neutron Brewing Co",
            "formatted_address": "47 Birchwood Lane, Amherst, MA 01002, USA",
            "geometry": {"lat": 42.3732, "lng": -72.5199},
            "types": ["cafe", "food", "point_of_interest"],
            "rating": 4.3,
            "user_ratings_total": 67,
            "opening_hours": {"open_now": True},
        },
        {
            "place_id": "ChIJfake_velox_03",
            "name": "Velox Dynamics HQ",
            "formatted_address": "890 Quantum Boulevard, Palo Alto, CA 94301, USA",
            "geometry": {"lat": 37.4419, "lng": -122.1430},
            "types": ["point_of_interest", "establishment"],
            "rating": 4.1,
            "user_ratings_total": 23,
            "opening_hours": {"open_now": True},
        },
    ],
    "addresses": {
        "1600 Amphitheatre Parkway, Mountain View, CA": {
            "lat": 37.4224764,
            "lng": -122.0842499,
            "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
        },
        "Sydney Opera House": {
            "lat": -33.856784,
            "lng": 151.215297,
            "formatted_address": "Bennelong Point, Sydney NSW 2000, Australia",
        },
        "1200 Innovation Drive, Boulder": {
            "lat": 40.0150,
            "lng": -105.2705,
            "formatted_address": "1200 Innovation Drive, Boulder, CO 80301, USA",
        },
        "47 Birchwood Lane, Amherst": {
            "lat": 42.3732,
            "lng": -72.5199,
            "formatted_address": "47 Birchwood Lane, Amherst, MA 01002, USA",
        },
        "890 Quantum Boulevard, Palo Alto": {
            "lat": 37.4419,
            "lng": -122.1430,
            "formatted_address": "890 Quantum Boulevard, Palo Alto, CA 94301, USA",
        },
    },
}


class GoogleMapsAPI:
    """
    Mock Google Maps MCP Server.

    STANDARD TOOL SET (7 tools) - Core mapping and navigation.

    Available tools:
    - maps_geocode: Convert address to coordinates
    - maps_reverse_geocode: Convert coordinates to address
    - maps_search_places: Search for places by query
    - maps_place_details: Get detailed place information
    - maps_distance_matrix: Calculate distances between points
    - maps_directions: Get route directions
    - maps_elevation: Get elevation data for coordinates

    NOT available (unlike Mapbox):
    - No offline geospatial calculations (distance, bearing, area)
    - No isochrone (reachability areas)
    - No buffer zones
    - No polygon operations
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)
        self.state["_place_query_epoch"] = 0
        self.state["_place_handles"] = {}

    def invalidate_transient_handles(self) -> None:
        """Invalidate volatile place handles so stale IDs must be refreshed."""
        self.state["_place_query_epoch"] += 1
        self.state["_place_handles"] = {}

    # =========================================================================
    # Tool 1: maps_geocode
    # =========================================================================

    def maps_geocode(
        self,
        address: str
    ) -> Dict[str, Any]:
        """
        Convert an address to geographic coordinates (geocoding).

        Takes a human-readable address and returns latitude/longitude
        coordinates along with the formatted address.

        Args:
            address (str): Address to geocode (e.g., "1600 Amphitheatre Parkway")

        Returns:
            dict: Geocoding result with coordinates
        """
        # Check for known addresses
        for addr, data in self.state["addresses"].items():
            if address.lower() in addr.lower():
                return {
                    "status": "OK",
                    "results": [{
                        "formatted_address": data["formatted_address"],
                        "geometry": {
                            "location": {
                                "lat": data["lat"],
                                "lng": data["lng"],
                            },
                        },
                    }],
                }

        # Check places
        for place in self.state["places"]:
            if address.lower() in place["name"].lower():
                return {
                    "status": "OK",
                    "results": [{
                        "formatted_address": place["formatted_address"],
                        "geometry": {
                            "location": {
                                "lat": place["geometry"]["lat"],
                                "lng": place["geometry"]["lng"],
                            },
                        },
                    }],
                }

        # Return mock result for unknown addresses
        return {
            "status": "OK",
            "results": [{
                "formatted_address": address,
                "geometry": {
                    "location": {
                        "lat": 40.7128,
                        "lng": -74.0060,
                    },
                },
            }],
        }

    # =========================================================================
    # Tool 2: maps_reverse_geocode
    # =========================================================================

    def maps_reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Convert coordinates to a human-readable address (reverse geocoding).

        Takes latitude and longitude and returns the closest matching address.

        Args:
            latitude (float): Latitude coordinate
            longitude (float): Longitude coordinate

        Returns:
            dict: Reverse geocoding result with address
        """
        # Check for nearby places
        for place in self.state["places"]:
            if (abs(place["geometry"]["lat"] - latitude) < 0.01 and
                abs(place["geometry"]["lng"] - longitude) < 0.01):
                return {
                    "status": "OK",
                    "results": [{
                        "formatted_address": place["formatted_address"],
                        "place_id": place["place_id"],
                    }],
                }

        # Return mock result
        return {
            "status": "OK",
            "results": [{
                "formatted_address": f"Location at {latitude:.4f}, {longitude:.4f}",
                "place_id": "mock_place_id",
            }],
        }

    # =========================================================================
    # Tool 3: maps_search_places
    # =========================================================================

    def maps_search_places(
        self,
        query: str,
        location: str = None,
        radius: int = 5000
    ) -> Dict[str, Any]:
        """
        Search for places matching a text query.

        Finds places like restaurants, cafes, landmarks, etc. based on
        the search query. Can be filtered by location and radius.

        Args:
            query (str): Search query (e.g., "coffee shops", "museums")
            location (str): Optional center point as "lat,lng"
            radius (int): Search radius in meters (default 5000)

        Returns:
            dict: List of matching places
        """
        self.state["_place_query_epoch"] += 1
        self.state["_place_handles"] = {}
        query_lower = query.lower()
        matching_places = []

        for idx, place in enumerate(self.state["places"]):
            if (query_lower in place["name"].lower() or
                any(query_lower in t for t in place["types"])):
                handle = f"gref_{self.state['_place_query_epoch']}_{idx}"
                self.state["_place_handles"][handle] = {
                    "place_id": place["place_id"],
                    "epoch": self.state["_place_query_epoch"],
                }
                matching_places.append({
                    "place_id": handle,
                    "source_place_id": place["place_id"],
                    "name": place["name"],
                    "formatted_address": place["formatted_address"],
                    "geometry": {"location": place["geometry"]},
                    "rating": place.get("rating"),
                    "types": place["types"],
                })

        if not matching_places:
            for idx, p in enumerate(self.state["places"][:3]):
                handle = f"gref_{self.state['_place_query_epoch']}_{idx}"
                self.state["_place_handles"][handle] = {
                    "place_id": p["place_id"],
                    "epoch": self.state["_place_query_epoch"],
                }
                matching_places.append({
                    "place_id": handle,
                    "source_place_id": p["place_id"],
                    "name": p["name"],
                    "formatted_address": p["formatted_address"],
                    "geometry": {"location": p["geometry"]},
                    "rating": p.get("rating"),
                    "types": p["types"],
                })

        return {
            "status": "OK",
            "query_epoch": self.state["_place_query_epoch"],
            "results": matching_places,
        }

    # =========================================================================
    # Tool 4: maps_place_details
    # =========================================================================

    def maps_place_details(
        self,
        place_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific place.

        Returns comprehensive details including address, phone, website,
        opening hours, reviews, and photos.

        Args:
            place_id (str): Google Place ID

        Returns:
            dict: Detailed place information
        """
        resolved = place_id
        if place_id in self.state["_place_handles"]:
            token = self.state["_place_handles"][place_id]
            if token["epoch"] != self.state["_place_query_epoch"]:
                return {"status": "STALE_REFERENCE", "error": "Place handle is stale. Re-run place search."}
            resolved = token["place_id"]

        for place in self.state["places"]:
            if place["place_id"] == resolved:
                return {
                    "status": "OK",
                    "result": {
                        "place_id": place["place_id"],
                        "name": place["name"],
                        "formatted_address": place["formatted_address"],
                        "geometry": {"location": place["geometry"]},
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                        "types": place["types"],
                        "opening_hours": place.get("opening_hours"),
                        "formatted_phone_number": "+1 234 567 890",
                        "website": f"https://example.com/{place['name'].lower().replace(' ', '-')}",
                    },
                }

        return {"status": "NOT_FOUND", "error": f"Place '{place_id}' not found"}

    # =========================================================================
    # Tool 5: maps_distance_matrix
    # =========================================================================

    def maps_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Calculate travel distances and times between multiple points.

        Computes distance and duration for all origin-destination pairs.
        Supports driving, walking, bicycling, and transit modes.

        Args:
            origins (List[str]): List of origin addresses or coordinates
            destinations (List[str]): List of destination addresses or coordinates
            mode (str): Travel mode (driving, walking, bicycling, transit)

        Returns:
            dict: Matrix of distances and durations
        """
        # Mock distance calculation
        rows = []
        for origin in origins:
            elements = []
            for dest in destinations:
                # Generate mock distance/duration
                distance_km = 5.0 + len(origin) % 10
                duration_min = 10 + len(dest) % 20

                if mode == "walking":
                    duration_min *= 4
                elif mode == "bicycling":
                    duration_min *= 2
                elif mode == "transit":
                    duration_min *= 1.5

                elements.append({
                    "status": "OK",
                    "distance": {
                        "text": f"{distance_km:.1f} km",
                        "value": int(distance_km * 1000),
                    },
                    "duration": {
                        "text": f"{int(duration_min)} mins",
                        "value": int(duration_min * 60),
                    },
                })
            rows.append({"elements": elements})

        return {
            "status": "OK",
            "origin_addresses": origins,
            "destination_addresses": destinations,
            "rows": rows,
        }

    # =========================================================================
    # Tool 6: maps_directions
    # =========================================================================

    def maps_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        alternatives: bool = False
    ) -> Dict[str, Any]:
        """
        Get turn-by-turn directions between two points.

        Returns detailed route information including steps, distance,
        duration, and polyline for map display.

        Args:
            origin (str): Starting point (address or coordinates)
            destination (str): End point (address or coordinates)
            mode (str): Travel mode (driving, walking, bicycling, transit)
            alternatives (bool): Whether to return alternative routes

        Returns:
            dict: Route directions with steps
        """
        # Mock route generation
        distance_km = 15.5
        duration_min = 25

        if mode == "walking":
            duration_min *= 4
        elif mode == "bicycling":
            duration_min *= 2

        route = {
            "summary": f"Via Main Street",
            "legs": [{
                "start_address": origin,
                "end_address": destination,
                "distance": {
                    "text": f"{distance_km:.1f} km",
                    "value": int(distance_km * 1000),
                },
                "duration": {
                    "text": f"{int(duration_min)} mins",
                    "value": int(duration_min * 60),
                },
                "steps": [
                    {
                        "instruction": "Head north on Main Street",
                        "distance": {"text": "0.5 km", "value": 500},
                        "duration": {"text": "2 mins", "value": 120},
                    },
                    {
                        "instruction": "Turn right onto Highway 101",
                        "distance": {"text": "10 km", "value": 10000},
                        "duration": {"text": "15 mins", "value": 900},
                    },
                    {
                        "instruction": "Take exit toward destination",
                        "distance": {"text": "5 km", "value": 5000},
                        "duration": {"text": "8 mins", "value": 480},
                    },
                ],
            }],
        }

        return {
            "status": "OK",
            "routes": [route],
        }

    # =========================================================================
    # Tool 7: maps_elevation
    # =========================================================================

    def maps_elevation(
        self,
        locations: List[str]
    ) -> Dict[str, Any]:
        """
        Get elevation data for specified locations.

        Returns elevation in meters for each provided coordinate.
        Useful for terrain analysis and route planning.

        Args:
            locations (List[str]): List of coordinates as "lat,lng" strings

        Returns:
            dict: Elevation data for each location
        """
        results = []
        for loc in locations:
            try:
                parts = loc.split(",")
                lat = float(parts[0])
                lng = float(parts[1])
                # Mock elevation based on coordinates
                elevation = 100 + (abs(lat) * 10) + (abs(lng) * 5)
                results.append({
                    "elevation": elevation,
                    "location": {"lat": lat, "lng": lng},
                    "resolution": 10.0,
                })
            except (ValueError, IndexError):
                results.append({
                    "elevation": 0,
                    "location": {"lat": 0, "lng": 0},
                    "resolution": 0,
                })

        return {
            "status": "OK",
            "results": results,
        }
