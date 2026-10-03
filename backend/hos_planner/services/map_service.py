import logging
import math
from functools import lru_cache

import requests
from django.conf import settings

from hos_planner import constants
from hos_planner.api.exceptions import MapServiceError, RouteNotFoundError

logger = logging.getLogger(__name__)

DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
AUTOCOMPLETE_URL = "https://api.openrouteservice.org/geocode/autocomplete"
REVERSE_URL = "https://api.openrouteservice.org/geocode/reverse"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_HEADERS = {"User-Agent": "hos-trip-planner/1.0"}
EARTH_RADIUS_MILES = 3958.8
METERS_PER_MILE = 1609.344


def location_to_coordinates(location):
    return [location["lng"], location["lat"]]


def request_route(coordinates):
    headers = {"Authorization": settings.ORS_API_KEY}
    body = {"coordinates": coordinates, "units": "mi"}

    try:
        response = requests.post(DIRECTIONS_URL, json=body, headers=headers, timeout=30)
    except requests.RequestException as error:
        logger.warning("OpenRouteService directions failed: %s", error)
        raise MapServiceError()

    if response.status_code == 400 or response.status_code == 404:
        logger.warning("OpenRouteService found no route: %s %s", response.status_code, response.text[:200])
        raise RouteNotFoundError()

    if response.status_code != 200:
        logger.warning("OpenRouteService directions failed: %s %s", response.status_code, response.text[:200])
        raise MapServiceError()

    return response.json()


def get_route(driver_request):
    coordinates = [
        location_to_coordinates(driver_request["current_location"]),
        location_to_coordinates(driver_request["pickup_location"]),
        location_to_coordinates(driver_request["dropoff_location"]),
    ]

    route_data = request_route(coordinates)
    route = route_data["features"][0]

    legs = []
    for segment in route["properties"]["segments"]:
        leg = {
            "miles": segment["distance"],
            "hours": segment["duration"] / 3600,
        }
        legs.append(leg)

    return {
        "legs": legs,
        "route_points": route["geometry"]["coordinates"],
    }


def miles_between(point_a, point_b):
    lng_a = math.radians(point_a[0])
    lat_a = math.radians(point_a[1])
    lng_b = math.radians(point_b[0])
    lat_b = math.radians(point_b[1])

    lat_difference = lat_b - lat_a
    lng_difference = lng_b - lng_a

    a = math.sin(lat_difference / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(lng_difference / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def point_at_mile(route_points, target_mile):
    miles_so_far = 0

    for index in range(1, len(route_points)):
        miles_so_far = miles_so_far + miles_between(route_points[index - 1], route_points[index])
        if miles_so_far >= target_mile:
            return route_points[index]

    return route_points[-1]


def build_fuel_station_query(point):
    radius = constants.FUEL_STATION_SEARCH_RADIUS_METERS
    lng = point[0]
    lat = point[1]
    return f'[out:json][timeout:25];nwr["amenity"="fuel"](around:{radius},{lat},{lng});out center;'


def search_fuel_stations(point):
    query = build_fuel_station_query(point)

    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, headers=OVERPASS_HEADERS, timeout=30)
    except requests.RequestException as error:
        logger.warning("Overpass fuel search failed: %s", error)
        raise MapServiceError()

    if response.status_code != 200:
        logger.warning("Overpass fuel search failed: %s %s", response.status_code, response.text[:200])
        raise MapServiceError()

    stations = []
    for element in response.json().get("elements", []):
        if "lat" in element:
            station_lat = element["lat"]
            station_lng = element["lon"]
        else:
            station_lat = element["center"]["lat"]
            station_lng = element["center"]["lon"]

        tags = element.get("tags", {})
        station = {
            "name": tags.get("name", "Fuel station"),
            "lng": station_lng,
            "lat": station_lat,
            "distance_meters": miles_between(point, [station_lng, station_lat]) * METERS_PER_MILE,
        }
        stations.append(station)

    return stations


def simplify_route_points(route_points):
    simple_points = []

    for index in range(0, len(route_points), constants.MAP_ROUTE_POINTS_STEP):
        simple_points.append(route_points[index])

    last_point = route_points[-1]
    if simple_points[-1] != last_point:
        simple_points.append(last_point)

    return simple_points


def search_locations(text):
    headers = {"Authorization": settings.ORS_API_KEY}
    params = {"text": text, "boundary.country": "US", "size": 5}

    try:
        response = requests.get(AUTOCOMPLETE_URL, params=params, headers=headers, timeout=15)
    except requests.RequestException as error:
        logger.warning("OpenRouteService location search failed: %s", error)
        raise MapServiceError()

    if response.status_code != 200:
        logger.warning("OpenRouteService location search failed: %s %s", response.status_code, response.text[:200])
        raise MapServiceError()

    locations = []
    for feature in response.json().get("features", []):
        location = {
            "name": feature["properties"]["label"],
            "lng": feature["geometry"]["coordinates"][0],
            "lat": feature["geometry"]["coordinates"][1],
        }
        locations.append(location)

    return locations


def format_coordinates(lat, lng):
    return f"{round(lat, 4)}, {round(lng, 4)}"


def reverse_location(lat, lng):
    headers = {"Authorization": settings.ORS_API_KEY}
    params = {"point.lat": lat, "point.lon": lng, "size": 1}

    try:
        response = requests.get(REVERSE_URL, params=params, headers=headers, timeout=15)
    except requests.RequestException as error:
        logger.warning("OpenRouteService reverse search failed: %s", error)
        raise MapServiceError()

    if response.status_code != 200:
        logger.warning("OpenRouteService reverse search failed: %s %s", response.status_code, response.text[:200])
        raise MapServiceError()

    name = format_coordinates(lat, lng)
    features = response.json().get("features", [])
    if len(features) > 0:
        name = features[0]["properties"]["label"]

    return {"name": name, "lat": lat, "lng": lng}


@lru_cache(maxsize=1000)
def find_place_name(lat, lng):
    headers = {"Authorization": settings.ORS_API_KEY}
    params = {"point.lat": lat, "point.lon": lng, "size": 1, "layers": "locality,localadmin,county"}

    try:
        response = requests.get(REVERSE_URL, params=params, headers=headers, timeout=15)
    except requests.RequestException as error:
        logger.warning("OpenRouteService place name failed: %s", error)
        raise MapServiceError()

    if response.status_code != 200:
        logger.warning("OpenRouteService place name failed: %s %s", response.status_code, response.text[:200])
        raise MapServiceError()

    features = response.json().get("features", [])
    if len(features) == 0:
        return None

    properties = features[0]["properties"]
    town = properties.get("locality") or properties.get("localadmin") or properties.get("county")
    state = properties.get("region_a")

    if town and state:
        return f"{town}, {state}"

    return properties.get("label")
