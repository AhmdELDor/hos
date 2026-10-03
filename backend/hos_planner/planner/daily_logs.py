from datetime import datetime, time, timedelta

from hos_planner import constants


def build_daily_logs(state):
    pieces = cut_segments_at_midnight(state["segments"])
    pieces = add_off_duty_before_and_after(pieces)
    pieces_by_day = group_pieces_by_day(pieces)

    daily_logs = []
    cycle_hours = state["cycle_used"]
    previous_status = None

    for day in pieces_by_day:
        day_pieces = pieces_by_day[day]
        cycle_hours = update_cycle_hours(cycle_hours, day_pieces)
        daily_log = build_one_day(day, day_pieces, cycle_hours, previous_status)
        daily_logs.append(daily_log)
        previous_status = day_pieces[-1]["status"]

    return daily_logs


def get_midnight_after(moment):
    next_day = moment.date() + timedelta(days=1)
    return datetime.combine(next_day, time(0, 0))


def get_midnight_before(moment):
    return datetime.combine(moment.date(), time(0, 0))


def make_piece(segment, start, end):
    hours = (end - start).total_seconds() / 3600

    miles = 0
    if segment["hours"] > 0:
        miles = segment["miles"] * hours / segment["hours"]

    return {
        "status": segment["status"],
        "start": start,
        "end": end,
        "hours": hours,
        "miles": miles,
        "note": segment["note"],
        "lng": segment["lng"],
        "lat": segment["lat"],
        "place": segment.get("place"),
    }


def cut_segments_at_midnight(segments):
    pieces = []

    for segment in segments:
        start = segment["start"]
        end = segment["end"]

        while start.date() < end.date():
            midnight = get_midnight_after(start)
            pieces.append(make_piece(segment, start, midnight))
            start = midnight

        if start < end:
            pieces.append(make_piece(segment, start, end))

    return pieces


def make_off_duty_piece(start, end, near_piece):
    off_duty_segment = {
        "status": constants.OFF_DUTY,
        "hours": 0,
        "miles": 0,
        "note": "Off duty",
        "lng": near_piece["lng"],
        "lat": near_piece["lat"],
        "place": near_piece["place"],
    }
    return make_piece(off_duty_segment, start, end)


def add_off_duty_before_and_after(pieces):
    first_piece = pieces[0]
    last_piece = pieces[-1]

    first_midnight = get_midnight_before(first_piece["start"])
    if first_piece["start"] > first_midnight:
        before = make_off_duty_piece(first_midnight, first_piece["start"], first_piece)
        pieces.insert(0, before)

    last_midnight = get_midnight_before(last_piece["end"])
    if last_piece["end"] > last_midnight:
        after = make_off_duty_piece(last_piece["end"], get_midnight_after(last_piece["end"]), last_piece)
        pieces.append(after)

    return pieces


def group_pieces_by_day(pieces):
    pieces_by_day = {}

    for piece in pieces:
        day = piece["start"].date()
        if day not in pieces_by_day:
            pieces_by_day[day] = []
        pieces_by_day[day].append(piece)

    return pieces_by_day


def update_cycle_hours(cycle_hours, day_pieces):
    for piece in day_pieces:
        if piece["status"] == constants.DRIVING or piece["status"] == constants.ON_DUTY:
            cycle_hours = cycle_hours + piece["hours"]

        if piece["note"] == "34-hour restart":
            cycle_hours = 0

    return cycle_hours


def build_one_day(day, day_pieces, cycle_hours, previous_status):
    totals = {
        constants.OFF_DUTY: 0,
        constants.SLEEPER_BERTH: 0,
        constants.DRIVING: 0,
        constants.ON_DUTY: 0,
    }
    miles_today = 0
    remarks = []

    for piece in day_pieces:
        totals[piece["status"]] = totals[piece["status"]] + piece["hours"]
        miles_today = miles_today + piece["miles"]

        if piece["status"] != previous_status:
            remark = {
                "time": piece["start"],
                "status": piece["status"],
                "note": piece["note"],
                "lng": piece["lng"],
                "lat": piece["lat"],
                "place": piece["place"],
            }
            remarks.append(remark)

        previous_status = piece["status"]

    for status in totals:
        totals[status] = round(totals[status], 2)

    on_duty_today = totals[constants.DRIVING] + totals[constants.ON_DUTY]
    available_tomorrow = max(constants.MAX_CYCLE_HOURS - cycle_hours, 0)

    return {
        "date": day,
        "segments": day_pieces,
        "totals": totals,
        "total_hours": round(sum(totals.values()), 2),
        "miles_today": round(miles_today, 1),
        "remarks": remarks,
        "recap": {
            "on_duty_today": round(on_duty_today, 2),
            "total_last_8_days": round(cycle_hours, 2),
            "available_tomorrow": round(available_tomorrow, 2),
        },
    }
