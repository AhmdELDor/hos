from hos_planner import constants


def cycle_hours_left(cycle_used):
    return constants.MAX_CYCLE_HOURS - cycle_used


def is_cycle_limit_reached(cycle_used):
    return cycle_hours_left(cycle_used) <= 0


def driving_hours_left(hours_driven):
    return constants.MAX_DRIVING_HOURS - hours_driven


def is_driving_limit_reached(hours_driven):
    return driving_hours_left(hours_driven) <= 0


def on_duty_hours_left(on_duty_hours):
    return constants.MAX_ON_DUTY_HOURS - on_duty_hours


def is_on_duty_limit_reached(on_duty_hours):
    return on_duty_hours_left(on_duty_hours) <= 0


def hours_left_before_break(hours_since_break):
    return constants.DRIVING_HOURS_BEFORE_BREAK - hours_since_break


def is_break_needed(hours_since_break):
    return hours_left_before_break(hours_since_break) <= 0


def miles_left_before_fuel(miles_since_fuel):
    return constants.MILES_BEFORE_FUEL - miles_since_fuel


def is_fuel_needed(miles_since_fuel):
    return miles_left_before_fuel(miles_since_fuel) <= 0
