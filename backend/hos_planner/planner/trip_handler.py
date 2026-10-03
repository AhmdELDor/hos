from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from hos_planner.api.exceptions import MapServiceError
from hos_planner.planner.daily_logs import build_daily_logs
from hos_planner.planner.fuel_planner import plan_fuel_stops
from hos_planner.planner.planner import create_driver_state, plan_drive
from hos_planner.services.map_service import find_place_name, get_route, simplify_route_points

PLACE_LOOKUP_WORKERS = 6


def get_place_key(item):
    return (round(item["lat"], 3), round(item["lng"], 3))


def look_up_place(place_key):
    try:
        return find_place_name(place_key[0], place_key[1])
    except MapServiceError:
        return None


def add_place_names(state):
    items = list(state["segments"])
    for stop_type in state["stops"]:
        items.extend(state["stops"][stop_type])

    place_keys = []
    for item in items:
        place_key = get_place_key(item)
        if place_key not in place_keys:
            place_keys.append(place_key)

    with ThreadPoolExecutor(max_workers=PLACE_LOOKUP_WORKERS) as executor:
        names = list(executor.map(look_up_place, place_keys))

    place_names = {}
    for place_key, name in zip(place_keys, names):
        place_names[place_key] = name

    for item in items:
        item["place"] = place_names[get_place_key(item)]


def plan_trip(driver_request):
    route = get_route(driver_request)

    start_time = datetime.now().replace(second=0, microsecond=0)
    state = create_driver_state(start_time, driver_request["cycle_used"], route)

    plan_fuel_stops(state)
    plan_drive(state)
    add_place_names(state)

    return {
        "start_time": state["start_time"],
        "full_legs_miles": state["full_legs_miles"],
        "locations": {
            "current": driver_request["current_location"],
            "pickup": driver_request["pickup_location"],
            "dropoff": driver_request["dropoff_location"],
        },
        "stops": state["stops"],
        "segments": state["segments"],
        "daily_logs": build_daily_logs(state),
        "route_points": simplify_route_points(state["route_points"]),
    }
