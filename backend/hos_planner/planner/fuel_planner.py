import math

from hos_planner import constants
from hos_planner.api.exceptions import MapServiceError
from hos_planner.services.map_service import point_at_mile, search_fuel_stations

# I make a fuel planner because it have a constraint while breaks are flexible depending on hours and fuel stops

def plan_fuel_stop_miles(full_legs_miles):
    if full_legs_miles <= constants.MILES_BEFORE_FUEL:
        return []

    number_of_stops = math.ceil(full_legs_miles / constants.FUEL_STOP_SPACING_MILES) - 1
    miles_between_stops = full_legs_miles / (number_of_stops + 1)

    fuel_stop_miles = []
    for stop_number in range(1, number_of_stops + 1):
        fuel_stop_miles.append(miles_between_stops * stop_number)

    return fuel_stop_miles


def plan_fuel_stops(state):
    planned_miles = plan_fuel_stop_miles(state["full_legs_miles"])

    fuel_stop_miles = []
    for planned_mile in planned_miles:
        station = find_fuel_station_near(state, planned_mile)
        state["stops"]["fuel"].append(station)
        fuel_stop_miles.append(station["mile"])

    return fuel_stop_miles


def choose_fuel_stop_type(hours_since_break):
    if hours_since_break >= constants.FUEL_AND_BREAK_FROM_HOURS and hours_since_break <= constants.DRIVING_HOURS_BEFORE_BREAK:
        return constants.FUEL_AND_BREAK

    return constants.FUEL_ONLY


def find_fuel_station_near(state, fuel_stop_mile):
    route_points = state["route_points"]
    search_mile = fuel_stop_mile

    while search_mile >= 0:
        point = point_at_mile(route_points, search_mile)

        try:
            stations = search_fuel_stations(point)
        except MapServiceError:
            break

        if len(stations) > 0:
            station = stations[0]
            station["mile"] = search_mile
            return station

        search_mile = search_mile - constants.FUEL_STATION_SEARCH_STEP_MILES

    point = point_at_mile(route_points, fuel_stop_mile)
    return {
        "name": "Fuel stop",
        "lng": point[0],
        "lat": point[1],
        "distance_meters": 0,
        "mile": fuel_stop_mile,
    }
