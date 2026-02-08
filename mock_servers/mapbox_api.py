# Mapbox MCP Server Mock
# Based on real Mapbox MCP server from mapbox/mcp-server
#
# Mapbox has 16 tools total, but we select:
# - All overlapping tools with Google Maps (core navigation)
# - Minimal extra geospatial tools to test adaptation
#
# OVERLAP WITH GOOGLE MAPS (5 tools):
#   1. mapbox_geocode - Forward geocoding (maps_geocode)
#   2. mapbox_reverse_geocode - Reverse geocoding (maps_reverse_geocode)
#   3. mapbox_search_places - Place search (maps_search_places)
#   4. mapbox_directions - Route directions (maps_directions)
#   5. mapbox_matrix - Distance matrix (maps_distance_matrix)
#
# MAPBOX-ONLY EXTRAS (5 tools - forces adaptation):
#   6. mapbox_distance - Calculate distance between two points (offline)
#   7. mapbox_bearing - Calculate compass bearing (offline)
#   8. mapbox_midpoint - Find midpoint between coords (offline)
#   9. mapbox_isochrone - Get reachability areas
#   10. mapbox_static_image - Generate map image
#
# Total: 10 tools (vs Google Maps' 7) - tests adaptation in both directions

from typing import Dict, Any, Optional, List
import math

DEFAULT_STATE = {
    "places": [
        {
            "id": "poi.123456",
            "name": "Mapbox HQ",
            "full_address": "740 15th Street NW, Washington, DC 20005, USA",
            "coordinates": [-77.0339, 38.9022],
            "place_type": ["poi"],
            "category": "office",
        },
        {
            "id": "poi.789012",
            "name": "National Mall",
            "full_address": "National Mall, Washington, DC, USA",
            "coordinates": [-77.0365, 38.8895],
            "place_type": ["poi", "landmark"],
            "category": "park",
        },
        {
            "id": "poi.345678",
            "name": "Capitol Coffee",
            "full_address": "100 First St SE, Washington, DC 20003, USA",
            "coordinates": [-77.0050, 38.8899],
            "place_type": ["poi"],
            "category": "cafe",
        },
        {
            "id": "poi.fake01",
            "name": "SkyLabs Research Center",
            "full_address": "1200 Innovation Drive, Boulder, CO 80301, USA",
            "coordinates": [-105.2705, 40.0150],
            "place_type": ["poi"],
            "category": "office",
        },
        {
            "id": "poi.fake02",
            "name": "Neutron Brewing Co",
            "full_address": "47 Birchwood Lane, Amherst, MA 01002, USA",
            "coordinates": [-72.5199, 42.3732],
            "place_type": ["poi"],
            "category": "cafe",
        },
        {
            "id": "poi.fake03",
            "name": "Velox Dynamics HQ",
            "full_address": "890 Quantum Boulevard, Palo Alto, CA 94301, USA",
            "coordinates": [-122.1430, 37.4419],
            "place_type": ["poi"],
            "category": "office",
        },
    ],
}


class MapboxAPI:
    """
    Mock Mapbox MCP Server.

    EXTENDED TOOL SET (10 tools) - More than Google Maps' 7 tools.

    OVERLAPPING TOOLS (work similar to Google Maps):
    - mapbox_geocode: Forward geocoding
    - mapbox_reverse_geocode: Reverse geocoding
    - mapbox_search_places: Search for POIs
    - mapbox_directions: Get route directions
    - mapbox_matrix: Distance/time matrix

    MAPBOX-ONLY TOOLS (Google Maps can't do these):
    - mapbox_distance: Offline distance calculation (Haversine)
    - mapbox_bearing: Compass bearing between points
    - mapbox_midpoint: Geographic midpoint
    - mapbox_isochrone: Reachability area polygons
    - mapbox_static_image: Generate static map images

    This tests model adaptation:
    - Google Maps → Mapbox: Model gains geospatial calculations
    - Mapbox → Google Maps: Model loses offline tools, must adapt
    """

    def __init__(self):
        self.state = None
        self._load_scenario({})

    def _load_scenario(self, scenario: dict):
        """Load a scenario state or reset to default."""
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state.update(scenario)
        self.state["_query_epoch"] = 0
        self.state["_feature_handles"] = {}

    def invalidate_transient_handles(self) -> None:
        """Invalidate volatile feature handles after failure/remount."""
        self.state["_query_epoch"] += 1
        self.state["_feature_handles"] = {}

    # =========================================================================
    # OVERLAPPING TOOLS (similar to Google Maps)
    # =========================================================================

    # Tool 1: mapbox_geocode (overlaps with maps_geocode)
    def mapbox_geocode(
        self,
        address: str,
        country: str = None
    ) -> Dict[str, Any]:
        """
        Convert an address to geographic coordinates (forward geocoding).

        Uses Mapbox Geocoding API to convert human-readable addresses
        to latitude/longitude coordinates.

        Args:
            address (str): Address to geocode
            country (str): Optional country code to limit results (e.g., "US")

        Returns:
            dict: Geocoding result with coordinates
        """
        self.state["_query_epoch"] += 1
        self.state["_feature_handles"] = {}
        address_lower = address.lower()

        # Check known places
        for place in self.state["places"]:
            if address_lower in place["name"].lower():
                handle = f"mbx_ref_{self.state['_query_epoch']}_{place['id']}"
                self.state["_feature_handles"][handle] = place["id"]
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "id": handle,
                        "source_id": place["id"],
                        "type": "Feature",
                        "place_name": place["full_address"],
                        "center": place["coordinates"],
                        "geometry": {
                            "type": "Point",
                            "coordinates": place["coordinates"],
                        },
                    }],
                }

        # Return mock result
        return {
            "type": "FeatureCollection",
            "features": [{
                "id": "address.mock",
                "type": "Feature",
                "place_name": address,
                "center": [-77.0369, 38.9072],
                "geometry": {
                    "type": "Point",
                    "coordinates": [-77.0369, 38.9072],
                },
            }],
        }

    # Tool 2: mapbox_reverse_geocode (overlaps with maps_reverse_geocode)
    def mapbox_reverse_geocode(
        self,
        longitude: float,
        latitude: float
    ) -> Dict[str, Any]:
        """
        Convert coordinates to a human-readable address (reverse geocoding).

        Takes longitude and latitude and returns the closest matching address.
        Note: Mapbox uses [longitude, latitude] order (GeoJSON standard).

        Args:
            longitude (float): Longitude coordinate
            latitude (float): Latitude coordinate

        Returns:
            dict: Reverse geocoding result with address
        """
        # Check nearby places
        for place in self.state["places"]:
            lng, lat = place["coordinates"]
            if abs(lng - longitude) < 0.01 and abs(lat - latitude) < 0.01:
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "id": place["id"],
                        "type": "Feature",
                        "place_name": place["full_address"],
                        "center": place["coordinates"],
                    }],
                }

        return {
            "type": "FeatureCollection",
            "features": [{
                "id": "address.mock",
                "type": "Feature",
                "place_name": f"Location at {latitude:.4f}, {longitude:.4f}",
                "center": [longitude, latitude],
            }],
        }

    # Tool 3: mapbox_search_places (overlaps with maps_search_places)
    def mapbox_search_places(
        self,
        query: str,
        proximity: str = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for places and points of interest.

        Searches the Mapbox database for places matching the query.
        Can be biased toward a specific location.

        Args:
            query (str): Search query (e.g., "coffee", "museum")
            proximity (str): Optional bias point as "lng,lat"
            limit (int): Maximum results to return

        Returns:
            dict: List of matching places
        """
        self.state["_query_epoch"] += 1
        self.state["_feature_handles"] = {}
        query_lower = query.lower()
        matching = []

        for idx, place in enumerate(self.state["places"]):
            if (query_lower in place["name"].lower() or
                query_lower in place.get("category", "").lower()):
                handle = f"mbx_ref_{self.state['_query_epoch']}_{idx}"
                self.state["_feature_handles"][handle] = place["id"]
                matching.append({
                    "id": handle,
                    "source_id": place["id"],
                    "type": "Feature",
                    "place_name": place["full_address"],
                    "center": place["coordinates"],
                    "properties": {
                        "name": place["name"],
                        "category": place.get("category"),
                    },
                })

        if not matching:
            for idx, p in enumerate(self.state["places"][:limit]):
                handle = f"mbx_ref_{self.state['_query_epoch']}_{idx}"
                self.state["_feature_handles"][handle] = p["id"]
                matching.append({
                    "id": handle,
                    "source_id": p["id"],
                    "type": "Feature",
                    "place_name": p["full_address"],
                    "center": p["coordinates"],
                    "properties": {"name": p["name"]},
                })

        return {
            "type": "FeatureCollection",
            "query_epoch": self.state["_query_epoch"],
            "features": matching[:limit],
        }

    # Tool 4: mapbox_directions (overlaps with maps_directions)
    def mapbox_directions(
        self,
        origin: str,
        destination: str,
        profile: str = "driving"
    ) -> Dict[str, Any]:
        """
        Get turn-by-turn directions between two points.

        Returns route information including distance, duration, and steps.
        Supports driving, walking, and cycling profiles.

        Args:
            origin (str): Starting point as "lng,lat" or address
            destination (str): End point as "lng,lat" or address
            profile (str): Routing profile (driving, walking, cycling)

        Returns:
            dict: Route directions with geometry
        """
        # Mock route
        distance_km = 12.5
        duration_min = 20

        if profile == "walking":
            duration_min *= 4
        elif profile == "cycling":
            duration_min *= 2

        return {
            "routes": [{
                "distance": distance_km * 1000,
                "duration": duration_min * 60,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [-77.0369, 38.9072],
                        [-77.0300, 38.9000],
                        [-77.0200, 38.8900],
                    ],
                },
                "legs": [{
                    "summary": "Via Constitution Ave",
                    "distance": distance_km * 1000,
                    "duration": duration_min * 60,
                    "steps": [
                        {
                            "maneuver": {"instruction": "Head east on K Street"},
                            "distance": 500,
                            "duration": 60,
                        },
                        {
                            "maneuver": {"instruction": "Turn right onto 15th Street"},
                            "distance": 8000,
                            "duration": 720,
                        },
                        {
                            "maneuver": {"instruction": "Continue to destination"},
                            "distance": 4000,
                            "duration": 420,
                        },
                    ],
                }],
            }],
            "waypoints": [
                {"name": "Origin", "location": [-77.0369, 38.9072]},
                {"name": "Destination", "location": [-77.0200, 38.8900]},
            ],
        }

    # Tool 5: mapbox_matrix (overlaps with maps_distance_matrix)
    def mapbox_matrix(
        self,
        coordinates: List[str],
        profile: str = "driving"
    ) -> Dict[str, Any]:
        """
        Calculate travel times and distances between multiple points.

        Returns a matrix of durations and distances for all coordinate pairs.

        Args:
            coordinates (List[str]): List of coordinates as "lng,lat" strings
            profile (str): Routing profile (driving, walking, cycling)

        Returns:
            dict: Matrix of durations and distances
        """
        n = len(coordinates)

        # Generate mock matrix
        durations = []
        distances = []

        for i in range(n):
            dur_row = []
            dist_row = []
            for j in range(n):
                if i == j:
                    dur_row.append(0)
                    dist_row.append(0)
                else:
                    base_dur = 600 + (i + j) * 60  # seconds
                    base_dist = 5000 + (i + j) * 1000  # meters

                    if profile == "walking":
                        base_dur *= 4
                    elif profile == "cycling":
                        base_dur *= 2

                    dur_row.append(base_dur)
                    dist_row.append(base_dist)

            durations.append(dur_row)
            distances.append(dist_row)

        return {
            "code": "Ok",
            "durations": durations,
            "distances": distances,
            "sources": [{"location": c.split(",")} for c in coordinates],
            "destinations": [{"location": c.split(",")} for c in coordinates],
        }

    # =========================================================================
    # MAPBOX-ONLY TOOLS (Google Maps can't do these)
    # =========================================================================

    # Tool 6: mapbox_distance (Mapbox-only - offline calculation)
    def mapbox_distance(
        self,
        point1: str,
        point2: str,
        unit: str = "kilometers"
    ) -> Dict[str, Any]:
        """
        Calculate the distance between two geographic coordinates.

        Uses the Haversine formula for accurate great-circle distance.
        This is an OFFLINE calculation - no API call needed!
        NOTE: This capability is NOT available in Google Maps MCP!

        Args:
            point1 (str): First coordinate as "lng,lat"
            point2 (str): Second coordinate as "lng,lat"
            unit (str): Output unit (kilometers, miles, meters)

        Returns:
            dict: Distance between the two points
        """
        try:
            lng1, lat1 = map(float, point1.split(","))
            lng2, lat2 = map(float, point2.split(","))
        except (ValueError, AttributeError):
            return {"error": "Invalid coordinate format. Use 'lng,lat'"}

        # Haversine formula
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_km = R * c

        if unit == "miles":
            distance = distance_km * 0.621371
        elif unit == "meters":
            distance = distance_km * 1000
        else:
            distance = distance_km

        return {
            "distance": round(distance, 3),
            "unit": unit,
            "from": {"longitude": lng1, "latitude": lat1},
            "to": {"longitude": lng2, "latitude": lat2},
        }

    # Tool 7: mapbox_bearing (Mapbox-only - offline calculation)
    def mapbox_bearing(
        self,
        point1: str,
        point2: str
    ) -> Dict[str, Any]:
        """
        Calculate the compass bearing from one point to another.

        Returns the initial bearing (forward azimuth) in degrees.
        This is an OFFLINE calculation - no API call needed!
        NOTE: This capability is NOT available in Google Maps MCP!

        Args:
            point1 (str): Starting coordinate as "lng,lat"
            point2 (str): Ending coordinate as "lng,lat"

        Returns:
            dict: Bearing in degrees (0-360, where 0=North)
        """
        try:
            lng1, lat1 = map(float, point1.split(","))
            lng2, lat2 = map(float, point2.split(","))
        except (ValueError, AttributeError):
            return {"error": "Invalid coordinate format. Use 'lng,lat'"}

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng = math.radians(lng2 - lng1)

        x = math.sin(delta_lng) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng))

        bearing_rad = math.atan2(x, y)
        bearing_deg = (math.degrees(bearing_rad) + 360) % 360

        # Convert to compass direction
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(bearing_deg / 45) % 8
        compass = directions[idx]

        return {
            "bearing": round(bearing_deg, 2),
            "compass_direction": compass,
            "from": {"longitude": lng1, "latitude": lat1},
            "to": {"longitude": lng2, "latitude": lat2},
        }

    # Tool 8: mapbox_midpoint (Mapbox-only - offline calculation)
    def mapbox_midpoint(
        self,
        point1: str,
        point2: str
    ) -> Dict[str, Any]:
        """
        Find the geographic midpoint between two coordinates.

        Calculates the point exactly halfway along the great circle path.
        This is an OFFLINE calculation - no API call needed!
        NOTE: This capability is NOT available in Google Maps MCP!

        Args:
            point1 (str): First coordinate as "lng,lat"
            point2 (str): Second coordinate as "lng,lat"

        Returns:
            dict: Midpoint coordinates
        """
        try:
            lng1, lat1 = map(float, point1.split(","))
            lng2, lat2 = map(float, point2.split(","))
        except (ValueError, AttributeError):
            return {"error": "Invalid coordinate format. Use 'lng,lat'"}

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lng1_rad = math.radians(lng1)
        delta_lng = math.radians(lng2 - lng1)

        bx = math.cos(lat2_rad) * math.cos(delta_lng)
        by = math.cos(lat2_rad) * math.sin(delta_lng)

        mid_lat = math.atan2(
            math.sin(lat1_rad) + math.sin(lat2_rad),
            math.sqrt((math.cos(lat1_rad) + bx) ** 2 + by ** 2)
        )
        mid_lng = lng1_rad + math.atan2(by, math.cos(lat1_rad) + bx)

        return {
            "midpoint": {
                "longitude": round(math.degrees(mid_lng), 6),
                "latitude": round(math.degrees(mid_lat), 6),
            },
            "from": {"longitude": lng1, "latitude": lat1},
            "to": {"longitude": lng2, "latitude": lat2},
        }

    # Tool 9: mapbox_isochrone (Mapbox-only)
    def mapbox_isochrone(
        self,
        coordinates: str,
        contours_minutes: List[int],
        profile: str = "driving"
    ) -> Dict[str, Any]:
        """
        Calculate areas reachable within specified time limits.

        Returns polygons representing areas that can be reached within
        the given time contours from the starting point.
        NOTE: This capability is NOT available in Google Maps MCP!

        Args:
            coordinates (str): Center point as "lng,lat"
            contours_minutes (List[int]): Time limits in minutes (e.g., [5, 10, 15])
            profile (str): Travel mode (driving, walking, cycling)

        Returns:
            dict: GeoJSON polygons for each time contour
        """
        try:
            lng, lat = map(float, coordinates.split(","))
        except (ValueError, AttributeError):
            return {"error": "Invalid coordinate format. Use 'lng,lat'"}

        # Generate mock isochrone polygons
        features = []
        for minutes in sorted(contours_minutes):
            # Rough approximation: driving ~1km/min, walking ~0.08km/min
            if profile == "walking":
                radius = minutes * 0.08
            elif profile == "cycling":
                radius = minutes * 0.3
            else:
                radius = minutes * 1.0

            # Create rough polygon (simplified)
            coords = []
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                new_lat = lat + (radius / 111) * math.cos(rad)
                new_lng = lng + (radius / 111) * math.sin(rad) / math.cos(math.radians(lat))
                coords.append([round(new_lng, 6), round(new_lat, 6)])
            coords.append(coords[0])  # Close polygon

            features.append({
                "type": "Feature",
                "properties": {
                    "contour": minutes,
                    "color": f"#{''.join(f'{int(255-minutes*10):02x}' for _ in range(3))}",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords],
                },
            })

        return {
            "type": "FeatureCollection",
            "features": features,
        }

    # Tool 10: mapbox_static_image (Mapbox-only)
    def mapbox_static_image(
        self,
        center: str,
        zoom: int = 12,
        width: int = 600,
        height: int = 400,
        style: str = "streets-v12",
        markers: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a static map image URL.

        Creates a URL for a static map image that can be embedded or downloaded.
        NOTE: This capability is NOT available in Google Maps MCP!

        Args:
            center (str): Map center as "lng,lat"
            zoom (int): Zoom level (0-22)
            width (int): Image width in pixels
            height (int): Image height in pixels
            style (str): Map style (streets-v12, satellite-v9, outdoors-v12)
            markers (List[str]): Optional markers as "lng,lat" strings

        Returns:
            dict: Static image URL and metadata
        """
        try:
            lng, lat = map(float, center.split(","))
        except (ValueError, AttributeError):
            return {"error": "Invalid coordinate format. Use 'lng,lat'"}

        # Build marker overlay string
        marker_overlay = ""
        if markers:
            marker_coords = ",".join(markers)
            marker_overlay = f"/pin-s+ff0000({marker_coords})"

        # Construct mock URL
        url = (
            f"https://api.mapbox.com/styles/v1/mapbox/{style}/static"
            f"{marker_overlay}/{lng},{lat},{zoom}/{width}x{height}"
            f"?access_token=YOUR_ACCESS_TOKEN"
        )

        return {
            "url": url,
            "center": {"longitude": lng, "latitude": lat},
            "zoom": zoom,
            "dimensions": {"width": width, "height": height},
            "style": style,
            "markers": markers or [],
        }
