import math

from datetime import timedelta

from hos_planner import constants
from hos_planner.planner import checkers
from hos_planner.planner.fuel_planner import choose_fuel_stop_type
from hos_planner.services.map_service import point_at_mile


def get_full_legs_miles(first_leg_miles, second_leg_miles):
    return first_leg_miles + second_leg_miles


def create_driver_state(start_time, cycle_used, route):
    first_leg = route["legs"][0]
    second_leg = route["legs"][1]

    return {
        "start_time": start_time,
        "cycle_used": cycle_used,
        "first_leg_miles": first_leg["miles"],
        "second_leg_miles": second_leg["miles"],
        "full_legs_miles": get_full_legs_miles(first_leg["miles"], second_leg["miles"]),
        "first_leg_hours": first_leg["hours"],
        "second_leg_hours": second_leg["hours"],
        "route_points": route["route_points"],
        "stops": {
            "pickup": [],
            "dropoff": [],
            "fuel": [],
            "break": [],
            "rest": [],
            "restart": [],
        },
        "segments": [],
    }


def get_total_driving_hours(state):
    return state["first_leg_hours"] + state["second_leg_hours"]


# get stops hours that are on-duty side (drop,pick and fuels)
def get_stops_on_duty_hours(state):
    number_of_fuel_stops = len(state["stops"]["fuel"])
    fuel_hours = number_of_fuel_stops * constants.FUEL_HOURS

    return constants.PICKUP_HOURS + constants.DROPOFF_HOURS + fuel_hours

# how much days needed depending on HOS rules
def estimate_work_days(state):
    driving_hours = get_total_driving_hours(state)
    stops_hours = get_stops_on_duty_hours(state)

    work_hours_per_day = constants.MAX_ON_DUTY_HOURS - constants.INSPECTION_HOURS - constants.BREAK_HOURS

    days_by_driving_limit = math.ceil(driving_hours / constants.MAX_DRIVING_HOURS)
    days_by_on_duty_limit = math.ceil((driving_hours + stops_hours) / work_hours_per_day)

    return max(days_by_driving_limit, days_by_on_duty_limit)


# all on-duty time to see whether we need a 34 reset or not
def get_trip_on_duty_hours(state):
    work_days = estimate_work_days(state)
    inspection_hours = work_days * 2 * constants.INSPECTION_HOURS

    return get_total_driving_hours(state) + get_stops_on_duty_hours(state) + inspection_hours


# descison for the restart or not
def needs_restart_during_trip(state):
    cycle_hours_available = checkers.cycle_hours_left(state["cycle_used"])
    return get_trip_on_duty_hours(state) > cycle_hours_available


def create_clock(state):
    return {
        "time": state["start_time"],
        "miles": 0,
        "driven_hours": 0,
        "on_duty_hours": 0,
        "since_break_hours": 0,
        "not_driving_in_a_row": 0,
        "cycle_hours": state["cycle_used"],
        "next_fuel_index": 0,
    }


def plan_drive(state):
    clock = create_clock(state)

    if checkers.cycle_hours_left(clock["cycle_hours"]) <= constants.INSPECTION_HOURS:
        take_restart(state, clock)
    else:
        start_day(state, clock)

    drive_leg(state, clock, state["first_leg_miles"], state["first_leg_hours"])
    pickup = add_segment(state, clock, constants.ON_DUTY, constants.PICKUP_HOURS, "Pickup")
    add_stop(state, "pickup", pickup, "Pickup")

    drive_leg(state, clock, state["second_leg_miles"], state["second_leg_hours"])
    dropoff = add_segment(state, clock, constants.ON_DUTY, constants.DROPOFF_HOURS, "Dropoff")
    add_stop(state, "dropoff", dropoff, "Dropoff")

    add_segment(state, clock, constants.ON_DUTY, constants.INSPECTION_HOURS, "Post-trip inspection")

    return state["segments"]


def drive_leg(state, clock, leg_miles, leg_hours):
    if leg_miles == 0:
        return

    miles_per_hour = leg_miles / leg_hours
    leg_end_mile = clock["miles"] + leg_miles
    miles_left = leg_miles

    while miles_left > 0:
        if checkers.is_cycle_limit_reached(clock["cycle_hours"]):
            take_restart(state, clock)

        elif checkers.is_driving_limit_reached(clock["driven_hours"]) or checkers.is_on_duty_limit_reached(clock["on_duty_hours"]):
            take_rest(state, clock)

        elif is_at_next_fuel_stop(state, clock):
            take_fuel_stop(state, clock)

        elif checkers.is_break_needed(clock["since_break_hours"]):
            take_break(state, clock)

        else:
            hours = hours_until_next_stop(state, clock, miles_left, miles_per_hour)

            if hours >= miles_left / miles_per_hour:
                hours = miles_left / miles_per_hour
                miles = miles_left
            else:
                miles = hours * miles_per_hour

            add_segment(state, clock, constants.DRIVING, hours, "Driving", miles)
            miles_left = round(leg_end_mile - clock["miles"], 6)


def hours_until_next_stop(state, clock, miles_left, miles_per_hour):
    hours_left_in_leg = miles_left / miles_per_hour
    hours_until_fuel = miles_to_next_fuel_stop(state, clock) / miles_per_hour

    return min(
        hours_left_in_leg,
        checkers.driving_hours_left(clock["driven_hours"]),
        checkers.on_duty_hours_left(clock["on_duty_hours"]),
        checkers.hours_left_before_break(clock["since_break_hours"]),
        checkers.cycle_hours_left(clock["cycle_hours"]),
        hours_until_fuel,
    )


def miles_to_next_fuel_stop(state, clock):
    fuel_stops = state["stops"]["fuel"]

    if clock["next_fuel_index"] >= len(fuel_stops):
        return state["full_legs_miles"]

    next_fuel_stop = fuel_stops[clock["next_fuel_index"]]
    return next_fuel_stop["mile"] - clock["miles"]


def is_at_next_fuel_stop(state, clock):
    fuel_stops = state["stops"]["fuel"]

    if clock["next_fuel_index"] >= len(fuel_stops):
        return False

    return miles_to_next_fuel_stop(state, clock) <= constants.ARRIVAL_TOLERANCE_MILES


def add_segment(state, clock, status, hours, note, miles=0):
    start = clock["time"]
    end = start + timedelta(hours=hours)
    point = point_at_mile(state["route_points"], clock["miles"])

    segment = {
        "status": status,
        "start": start,
        "end": end,
        "hours": hours,
        "miles": miles,
        "start_mile": clock["miles"],
        "note": note,
        "lng": point[0],
        "lat": point[1],
    }
    state["segments"].append(segment)

    clock["time"] = end
    clock["on_duty_hours"] = round(clock["on_duty_hours"] + hours, 6)

    if status == constants.DRIVING or status == constants.ON_DUTY:
        clock["cycle_hours"] = round(clock["cycle_hours"] + hours, 6)

    if status == constants.DRIVING:
        clock["driven_hours"] = round(clock["driven_hours"] + hours, 6)
        clock["since_break_hours"] = round(clock["since_break_hours"] + hours, 6)
        clock["miles"] = round(clock["miles"] + miles, 6)
        clock["not_driving_in_a_row"] = 0
    else:
        clock["not_driving_in_a_row"] = clock["not_driving_in_a_row"] + hours
        if clock["not_driving_in_a_row"] >= constants.BREAK_HOURS:
            clock["since_break_hours"] = 0

    return segment


def add_stop(state, stop_type, segment, name):
    stop = {
        "name": name,
        "lng": segment["lng"],
        "lat": segment["lat"],
        "mile": segment["start_mile"],
        "start": segment["start"],
        "end": segment["end"],
    }
    state["stops"][stop_type].append(stop)


def start_day(state, clock):
    add_segment(state, clock, constants.ON_DUTY, constants.INSPECTION_HOURS, "Pre-trip inspection")


def end_day(state, clock):
    if clock["on_duty_hours"] > 0:
        add_segment(state, clock, constants.ON_DUTY, constants.INSPECTION_HOURS, "Post-trip inspection")


def take_break(state, clock):
    segment = add_segment(state, clock, constants.OFF_DUTY, constants.BREAK_HOURS, "30-minute break")
    add_stop(state, "break", segment, "30-minute break")


def take_fuel_stop(state, clock):
    fuel_stop = state["stops"]["fuel"][clock["next_fuel_index"]]
    fuel_stop["start"] = clock["time"]

    stop_type = choose_fuel_stop_type(clock["since_break_hours"])

    if stop_type == constants.FUEL_AND_BREAK:
        add_segment(state, clock, constants.ON_DUTY, constants.FUEL_AND_BREAK_ON_DUTY_HOURS, "Fuel stop")
        add_segment(state, clock, constants.OFF_DUTY, constants.FUEL_AND_BREAK_OFF_DUTY_HOURS, "Break after fuel")
    else:
        add_segment(state, clock, constants.ON_DUTY, constants.FUEL_HOURS, "Fuel stop")

    fuel_stop["end"] = clock["time"]
    fuel_stop["stop_type"] = stop_type
    clock["next_fuel_index"] = clock["next_fuel_index"] + 1


def take_rest(state, clock):
    end_day(state, clock)

    segment = add_segment(state, clock, constants.SLEEPER_BERTH, constants.REST_HOURS, "10-hour rest")
    add_stop(state, "rest", segment, "10-hour rest")

    clock["driven_hours"] = 0
    clock["on_duty_hours"] = 0
    clock["since_break_hours"] = 0

    start_day(state, clock)


def take_restart(state, clock):
    end_day(state, clock)

    segment = add_segment(state, clock, constants.OFF_DUTY, constants.RESTART_HOURS, "34-hour restart")
    add_stop(state, "restart", segment, "34-hour restart")

    clock["driven_hours"] = 0
    clock["on_duty_hours"] = 0
    clock["since_break_hours"] = 0
    clock["cycle_hours"] = 0

    start_day(state, clock)
