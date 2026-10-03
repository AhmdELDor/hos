from datetime import datetime
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APISimpleTestCase

from hos_planner.api.exceptions import MapServiceError, RouteNotFoundError
from hos_planner.planner import checkers
from hos_planner.planner import daily_logs, fuel_planner, planner, trip_handler
from hos_planner.services import map_service

PLAN_DRIVE_URL = "/api/plan-drive/"

STRAIGHT_ROUTE = [[-100.0, 30.0], [-100.0, 31.0], [-100.0, 32.0], [-100.0, 33.0]]


def fake_route(first_leg_miles, second_leg_miles, miles_per_hour=50):
    return {
        "legs": [
            {"miles": first_leg_miles, "hours": first_leg_miles / miles_per_hour},
            {"miles": second_leg_miles, "hours": second_leg_miles / miles_per_hour},
        ],
        "route_points": STRAIGHT_ROUTE,
    }

FAKE_ROUTE = {
    "legs": [
        {"miles": 186.6, "hours": 4.75},
        {"miles": 907.2, "hours": 20.13},
    ],
    "route_points": [[-87.62, 41.87], [-86.15, 39.76], [-96.79, 32.77]],
}

EXXON = {"name": "Exxon", "lng": -86.5, "lat": 37.0, "distance_meters": 500}

FAKE_ORS_RESPONSE = {
    "features": [
        {
            "properties": {
                "segments": [
                    {"distance": 186.6, "duration": 17100},
                    {"distance": 907.2, "duration": 72468},
                ]
            },
            "geometry": {"coordinates": [[-87.62, 41.87], [-86.15, 39.76], [-96.79, 32.77]]},
        }
    ]
}


def fake_ors_reply(status_code, body=None):
    reply = Mock()
    reply.status_code = status_code
    reply.json.return_value = body
    reply.text = "fake reply"
    return reply


def valid_driver_request():
    return {
        "current_location": {"lat": 41.87, "lng": -87.62, "name": "Chicago, IL"},
        "pickup_location": {"lat": 39.76, "lng": -86.15, "name": "Indianapolis, IN"},
        "dropoff_location": {"lat": 32.77, "lng": -96.79, "name": "Dallas, TX"},
        "cycle_used": 20,
    }


class PlanDriveInputTests(APISimpleTestCase):
    @patch("hos_planner.planner.trip_handler.find_place_name", return_value="Joplin, MO")
    @patch("hos_planner.planner.fuel_planner.search_fuel_stations", return_value=[EXXON])
    @patch("hos_planner.planner.trip_handler.get_route", return_value=FAKE_ROUTE)
    def test_valid_request(self, fake_get_route, fake_search, fake_place_name):
        response = self.client.post(PLAN_DRIVE_URL, valid_driver_request(), format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        trip = response.data["data"]
        self.assertEqual(trip["full_legs_miles"], 186.6 + 907.2)
        self.assertEqual(len(trip["route_points"]), 2)
        self.assertEqual(len(trip["stops"]["fuel"]), 1)
        self.assertEqual(len(trip["stops"]["pickup"]), 1)
        self.assertEqual(len(trip["stops"]["dropoff"]), 1)
        self.assertEqual(trip["segments"][0]["note"], "Pre-trip inspection")
        self.assertEqual(trip["segments"][-1]["note"], "Post-trip inspection")

    @patch("hos_planner.planner.trip_handler.get_route", side_effect=RouteNotFoundError())
    def test_route_not_found(self, fake_get_route):
        response = self.client.post(PLAN_DRIVE_URL, valid_driver_request(), format="json")

        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["message"], "No driving route was found between these locations.")

    @patch("hos_planner.planner.trip_handler.get_route", side_effect=MapServiceError())
    def test_map_service_down(self, fake_get_route):
        response = self.client.post(PLAN_DRIVE_URL, valid_driver_request(), format="json")

        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.data["success"])

    def test_missing_fields(self):
        response = self.client.post(PLAN_DRIVE_URL, {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertIn("pickup_location", response.data["error"]["details"])
        self.assertIn("cycle_used", response.data["error"]["details"])

    def test_cycle_used_above_70(self):
        data = valid_driver_request()
        data["cycle_used"] = 75

        response = self.client.post(PLAN_DRIVE_URL, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("cycle_used", response.data["error"]["details"])

    def test_cycle_used_below_0(self):
        data = valid_driver_request()
        data["cycle_used"] = -1

        response = self.client.post(PLAN_DRIVE_URL, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("cycle_used", response.data["error"]["details"])

    def test_latitude_out_of_range(self):
        data = valid_driver_request()
        data["current_location"]["lat"] = 120

        response = self.client.post(PLAN_DRIVE_URL, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("current_location", response.data["error"]["details"])

    def test_same_pickup_and_dropoff(self):
        data = valid_driver_request()
        data["dropoff_location"] = data["pickup_location"]

        response = self.client.post(PLAN_DRIVE_URL, data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.data["error"]["details"])

    def test_get_not_allowed(self):
        response = self.client.get(PLAN_DRIVE_URL)

        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.data["success"])


class CycleCheckerTests(SimpleTestCase):
    def test_cycle_hours_left(self):
        self.assertEqual(checkers.cycle_hours_left(20), 50)
        self.assertEqual(checkers.cycle_hours_left(0), 70)
        self.assertEqual(checkers.cycle_hours_left(69.5), 0.5)

    def test_cycle_limit_not_reached(self):
        self.assertFalse(checkers.is_cycle_limit_reached(20))
        self.assertFalse(checkers.is_cycle_limit_reached(69.5))

    def test_cycle_limit_reached(self):
        self.assertTrue(checkers.is_cycle_limit_reached(70))


class DrivingCheckerTests(SimpleTestCase):
    def test_driving_hours_left(self):
        self.assertEqual(checkers.driving_hours_left(0), 11)
        self.assertEqual(checkers.driving_hours_left(7.5), 3.5)

    def test_driving_limit(self):
        self.assertFalse(checkers.is_driving_limit_reached(10.5))
        self.assertTrue(checkers.is_driving_limit_reached(11))


class OnDutyCheckerTests(SimpleTestCase):
    def test_on_duty_hours_left(self):
        self.assertEqual(checkers.on_duty_hours_left(0), 14)
        self.assertEqual(checkers.on_duty_hours_left(12.5), 1.5)

    def test_on_duty_limit(self):
        self.assertFalse(checkers.is_on_duty_limit_reached(13.5))
        self.assertTrue(checkers.is_on_duty_limit_reached(14))


class BreakCheckerTests(SimpleTestCase):
    def test_hours_left_before_break(self):
        self.assertEqual(checkers.hours_left_before_break(0), 8)
        self.assertEqual(checkers.hours_left_before_break(6), 2)

    def test_break_needed(self):
        self.assertFalse(checkers.is_break_needed(7.5))
        self.assertTrue(checkers.is_break_needed(8))


class FuelCheckerTests(SimpleTestCase):
    def test_miles_left_before_fuel(self):
        self.assertEqual(checkers.miles_left_before_fuel(0), 1000)
        self.assertEqual(checkers.miles_left_before_fuel(950), 50)

    def test_fuel_needed(self):
        self.assertFalse(checkers.is_fuel_needed(999))
        self.assertTrue(checkers.is_fuel_needed(1000))


class DriverStateTests(SimpleTestCase):
    def test_state_saves_the_inputs(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 1200))

        self.assertEqual(state["start_time"], datetime(2026, 10, 1, 8, 0))
        self.assertEqual(state["cycle_used"], 20)
        self.assertEqual(state["first_leg_hours"], 2)
        self.assertEqual(state["second_leg_hours"], 24)

    def test_state_saves_leg_miles(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 1200))

        self.assertEqual(state["first_leg_miles"], 100)
        self.assertEqual(state["second_leg_miles"], 1200)
        self.assertEqual(state["full_legs_miles"], 1300)
        self.assertEqual(state["route_points"], STRAIGHT_ROUTE)
        self.assertEqual(state["stops"]["fuel"], [])
        self.assertEqual(state["stops"]["break"], [])


class FullLegsMilesTests(SimpleTestCase):
    def test_adds_both_legs(self):
        self.assertEqual(planner.get_full_legs_miles(100, 1200), 1300)
        self.assertEqual(planner.get_full_legs_miles(600, 600), 1200)


class MapServiceTests(SimpleTestCase):
    @patch("hos_planner.services.map_service.requests.post")
    def test_get_route_returns_both_legs(self, fake_post):
        fake_post.return_value = fake_ors_reply(200, FAKE_ORS_RESPONSE)

        route = map_service.get_route(valid_driver_request())

        self.assertEqual(route["legs"][0]["miles"], 186.6)
        self.assertEqual(route["legs"][0]["hours"], 4.75)
        self.assertEqual(route["legs"][1]["miles"], 907.2)
        self.assertEqual(len(route["route_points"]), 3)

    @patch("hos_planner.services.map_service.requests.post")
    def test_unreachable_location(self, fake_post):
        fake_post.return_value = fake_ors_reply(404)

        with self.assertRaises(RouteNotFoundError):
            map_service.get_route(valid_driver_request())

    @patch("hos_planner.services.map_service.requests.post")
    def test_map_service_down(self, fake_post):
        fake_post.return_value = fake_ors_reply(503)

        with self.assertRaises(MapServiceError):
            map_service.get_route(valid_driver_request())


class PointAtMileTests(SimpleTestCase):
    def test_one_degree_of_latitude_is_about_69_miles(self):
        miles = map_service.miles_between([-100.0, 30.0], [-100.0, 31.0])

        self.assertAlmostEqual(miles, 69.1, places=1)

    def test_point_at_mile(self):
        self.assertEqual(map_service.point_at_mile(STRAIGHT_ROUTE, 50), [-100.0, 31.0])
        self.assertEqual(map_service.point_at_mile(STRAIGHT_ROUTE, 100), [-100.0, 32.0])

    def test_mile_after_the_end_returns_last_point(self):
        self.assertEqual(map_service.point_at_mile(STRAIGHT_ROUTE, 5000), [-100.0, 33.0])


def new_state():
    return planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 1200))


class FuelStationTests(SimpleTestCase):
    @patch("hos_planner.planner.fuel_planner.search_fuel_stations")
    def test_station_found_at_the_fuel_mile(self, fake_search):
        fake_search.return_value = [{"name": "Exxon", "lng": -100.0, "lat": 31.0, "distance_meters": 500}]

        station = fuel_planner.find_fuel_station_near(new_state(), 100)

        self.assertEqual(station["name"], "Exxon")
        self.assertEqual(station["mile"], 100)

    @patch("hos_planner.planner.fuel_planner.search_fuel_stations")
    def test_search_steps_back_when_nothing_found(self, fake_search):
        exxon = {"name": "Exxon", "lng": -100.0, "lat": 31.0, "distance_meters": 500}
        fake_search.side_effect = [[], [], [exxon]]

        station = fuel_planner.find_fuel_station_near(new_state(), 100)

        self.assertEqual(station["name"], "Exxon")
        self.assertEqual(station["mile"], 80)

    @patch("hos_planner.planner.fuel_planner.search_fuel_stations", return_value=[])
    def test_no_station_found_uses_the_route_point(self, fake_search):
        station = fuel_planner.find_fuel_station_near(new_state(), 100)

        self.assertEqual(station["name"], "Fuel stop")
        self.assertEqual(station["mile"], 100)
        self.assertEqual(fake_search.call_count, 11)


class FuelStopTypeTests(SimpleTestCase):
    def test_fuel_only_before_6_hours(self):
        self.assertEqual(fuel_planner.choose_fuel_stop_type(0), "fuel_only")
        self.assertEqual(fuel_planner.choose_fuel_stop_type(5.5), "fuel_only")

    def test_fuel_and_break_between_6_and_8_hours(self):
        self.assertEqual(fuel_planner.choose_fuel_stop_type(6), "fuel_and_break")
        self.assertEqual(fuel_planner.choose_fuel_stop_type(7.25), "fuel_and_break")
        self.assertEqual(fuel_planner.choose_fuel_stop_type(8), "fuel_and_break")


class FuelStopMilesTests(SimpleTestCase):
    def test_no_fuel_needed_up_to_1000_miles(self):
        self.assertEqual(fuel_planner.plan_fuel_stop_miles(950), [])
        self.assertEqual(fuel_planner.plan_fuel_stop_miles(1000), [])

    def test_one_stop_in_the_middle(self):
        self.assertEqual(fuel_planner.plan_fuel_stop_miles(1300), [650])

    def test_stops_are_spaced_evenly(self):
        self.assertEqual(fuel_planner.plan_fuel_stop_miles(2700), [900, 1800])

    def test_gaps_stay_under_900_miles(self):
        for full_legs_miles in [1001, 1999, 2500, 4321]:
            fuel_stop_miles = fuel_planner.plan_fuel_stop_miles(full_legs_miles)
            previous_mile = 0
            for fuel_stop_mile in fuel_stop_miles + [full_legs_miles]:
                self.assertLessEqual(fuel_stop_mile - previous_mile, 900)
                previous_mile = fuel_stop_mile


class PlanFuelStopsTests(SimpleTestCase):
    @patch("hos_planner.planner.fuel_planner.search_fuel_stations")
    def test_stations_are_added_to_stops(self, fake_search):
        fake_search.return_value = [{"name": "Exxon", "lng": -100.0, "lat": 31.0, "distance_meters": 500}]
        state = new_state()
        state["full_legs_miles"] = 1300

        fuel_stop_miles = fuel_planner.plan_fuel_stops(state)

        self.assertEqual(fuel_stop_miles, [650])
        self.assertEqual(len(state["stops"]["fuel"]), 1)
        self.assertEqual(state["stops"]["fuel"][0]["name"], "Exxon")

    @patch("hos_planner.planner.fuel_planner.search_fuel_stations")
    def test_short_trip_adds_no_stops(self, fake_search):
        state = new_state()
        state["full_legs_miles"] = 800

        self.assertEqual(fuel_planner.plan_fuel_stops(state), [])
        self.assertEqual(state["stops"]["fuel"], [])
        self.assertEqual(fake_search.call_count, 0)


def fuel_stop(mile):
    return {"name": "Exxon", "lng": -100.0, "lat": 31.0, "distance_meters": 500, "mile": mile}


class WorkDaysTests(SimpleTestCase):
    def test_worked_example_takes_3_days(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 1200))
        state["stops"]["fuel"].append(fuel_stop(650))

        self.assertEqual(planner.get_total_driving_hours(state), 26)
        self.assertEqual(planner.get_stops_on_duty_hours(state), 2.5)
        self.assertEqual(planner.estimate_work_days(state), 3)

    def test_short_trip_takes_1_day(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 300))

        self.assertEqual(planner.estimate_work_days(state), 1)

    def test_no_restart_when_cycle_is_enough(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 20, fake_route(100, 1200))
        state["stops"]["fuel"].append(fuel_stop(650))

        self.assertEqual(planner.get_trip_on_duty_hours(state), 31.5)
        self.assertFalse(planner.needs_restart_during_trip(state))

    def test_restart_when_cycle_is_almost_used(self):
        state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), 60, fake_route(100, 1200))
        state["stops"]["fuel"].append(fuel_stop(650))

        self.assertTrue(planner.needs_restart_during_trip(state))


LONG_ROUTE = [[-100.0, 30.0 + index * 0.02] for index in range(1000)]


def walk_state(first_leg_miles, second_leg_miles, cycle_used, fuel_stop_miles):
    route = fake_route(first_leg_miles, second_leg_miles)
    route["route_points"] = LONG_ROUTE
    state = planner.create_driver_state(datetime(2026, 10, 1, 8, 0), cycle_used, route)
    for mile in fuel_stop_miles:
        state["stops"]["fuel"].append(fuel_stop(mile))
    return state


def total_hours(segments, status):
    hours = 0
    for segment in segments:
        if segment["status"] == status:
            hours = hours + segment["hours"]
    return hours


class PlanDriveTests(SimpleTestCase):
    def test_worked_example(self):
        state = walk_state(100, 1200, 20, [650])

        segments = planner.plan_drive(state)

        self.assertEqual(segments[0]["note"], "Pre-trip inspection")
        self.assertEqual(segments[-1]["note"], "Post-trip inspection")
        self.assertEqual(segments[-1]["end"], datetime(2026, 10, 3, 12, 30))
        self.assertEqual(total_hours(segments, "driving"), 26)
        self.assertEqual(len(state["stops"]["break"]), 2)
        self.assertEqual(len(state["stops"]["rest"]), 2)
        self.assertEqual(len(state["stops"]["restart"]), 0)
        self.assertEqual(state["stops"]["fuel"][0]["start"], datetime(2026, 10, 2, 10, 0))

    def test_no_driving_more_than_11_hours_between_rests(self):
        state = walk_state(100, 2500, 0, [900, 1800])

        driven = 0
        for segment in planner.plan_drive(state):
            if segment["status"] == "driving":
                driven = driven + segment["hours"]
            if segment["status"] == "sleeper_berth":
                driven = 0
            self.assertLessEqual(driven, 11)

    def test_restart_when_cycle_runs_out(self):
        state = walk_state(100, 300, 65, [])

        segments = planner.plan_drive(state)

        self.assertEqual(len(state["stops"]["restart"]), 1)
        self.assertEqual(total_hours(segments, "driving"), 8)

    def test_restart_first_when_cycle_is_full(self):
        state = walk_state(100, 300, 70, [])

        segments = planner.plan_drive(state)

        self.assertEqual(segments[0]["note"], "34-hour restart")
        self.assertEqual(segments[1]["note"], "Pre-trip inspection")

    def test_fuel_stop_counts_as_break_after_6_hours(self):
        state = walk_state(50, 1100, 20, [400])

        segments = planner.plan_drive(state)

        self.assertEqual(state["stops"]["fuel"][0]["stop_type"], "fuel_and_break")
        notes = [segment["note"] for segment in segments]
        fuel_index = notes.index("Fuel stop")
        self.assertEqual(notes[fuel_index + 1], "Break after fuel")


class PlanTripTests(SimpleTestCase):
    @patch("hos_planner.planner.trip_handler.find_place_name", return_value="Joplin, MO")
    @patch("hos_planner.planner.fuel_planner.search_fuel_stations")
    @patch("hos_planner.planner.trip_handler.get_route")
    def test_plan_trip_runs_every_step(self, fake_get_route, fake_search, fake_place_name):
        route = fake_route(100, 1200)
        route["route_points"] = LONG_ROUTE
        fake_get_route.return_value = route
        fake_search.return_value = [{"name": "Exxon", "lng": -100.0, "lat": 39.0, "distance_meters": 500}]

        trip = trip_handler.plan_trip(valid_driver_request())

        self.assertEqual(trip["full_legs_miles"], 1300)
        self.assertEqual(len(trip["stops"]["fuel"]), 1)
        self.assertEqual(len(trip["stops"]["pickup"]), 1)
        self.assertEqual(len(trip["stops"]["dropoff"]), 1)
        self.assertEqual(trip["segments"][0]["note"], "Pre-trip inspection")
        self.assertEqual(trip["segments"][-1]["note"], "Post-trip inspection")


class SimplifyRoutePointsTests(SimpleTestCase):
    def test_keeps_every_10th_point_and_the_last(self):
        points = []
        for index in range(25):
            points.append([index, index])

        simple_points = map_service.simplify_route_points(points)

        self.assertEqual(simple_points, [[0, 0], [10, 10], [20, 20], [24, 24]])

    def test_short_route_keeps_first_and_last(self):
        self.assertEqual(map_service.simplify_route_points(STRAIGHT_ROUTE), [STRAIGHT_ROUTE[0], STRAIGHT_ROUTE[-1]])


def worked_example_logs():
    state = walk_state(100, 1200, 20, [650])
    planner.plan_drive(state)
    return daily_logs.build_daily_logs(state)


class DailyLogsTests(SimpleTestCase):
    def test_worked_example_has_3_days(self):
        logs = worked_example_logs()

        self.assertEqual(len(logs), 3)
        self.assertEqual(str(logs[0]["date"]), "2026-10-01")
        self.assertEqual(str(logs[2]["date"]), "2026-10-03")

    def test_every_day_is_24_hours(self):
        for log in worked_example_logs():
            self.assertEqual(log["total_hours"], 24)

    def test_day_totals(self):
        logs = worked_example_logs()

        self.assertEqual(logs[0]["totals"], {"off_duty": 8.5, "sleeper_berth": 2.5, "driving": 11, "on_duty": 2})
        self.assertEqual(logs[1]["totals"], {"off_duty": 0.5, "sleeper_berth": 11, "driving": 11, "on_duty": 1.5})
        self.assertEqual(logs[2]["totals"], {"off_duty": 11.5, "sleeper_berth": 6.5, "driving": 4, "on_duty": 2})

    def test_miles_per_day(self):
        logs = worked_example_logs()

        self.assertEqual(logs[0]["miles_today"], 550)
        self.assertEqual(logs[1]["miles_today"], 550)
        self.assertEqual(logs[2]["miles_today"], 200)

    def test_rest_is_cut_at_midnight(self):
        logs = worked_example_logs()

        last_piece_day_1 = logs[0]["segments"][-1]
        first_piece_day_2 = logs[1]["segments"][0]
        self.assertEqual(last_piece_day_1["status"], "sleeper_berth")
        self.assertEqual(last_piece_day_1["end"], datetime(2026, 10, 2, 0, 0))
        self.assertEqual(first_piece_day_2["status"], "sleeper_berth")
        self.assertEqual(first_piece_day_2["start"], datetime(2026, 10, 2, 0, 0))

    def test_recap(self):
        logs = worked_example_logs()

        self.assertEqual(logs[0]["recap"], {"on_duty_today": 13, "total_last_8_days": 33, "available_tomorrow": 37})
        self.assertEqual(logs[2]["recap"]["total_last_8_days"], 51.5)

    def test_restart_resets_the_recap(self):
        state = walk_state(100, 300, 65, [])
        planner.plan_drive(state)

        logs = daily_logs.build_daily_logs(state)

        for log in logs:
            self.assertEqual(log["total_hours"], 24)
        self.assertLess(logs[-1]["recap"]["total_last_8_days"], 70)


FAKE_OVERPASS_RESPONSE = {
    "elements": [
        {"type": "node", "lat": 31.0, "lon": -100.0, "tags": {"amenity": "fuel", "name": "Exxon"}},
        {"type": "way", "center": {"lat": 31.01, "lon": -100.0}, "tags": {"amenity": "fuel"}},
    ]
}


class OverpassSearchTests(SimpleTestCase):
    @patch("hos_planner.services.map_service.requests.post")
    def test_reads_points_and_buildings(self, fake_post):
        fake_post.return_value = fake_ors_reply(200, FAKE_OVERPASS_RESPONSE)

        stations = map_service.search_fuel_stations([-100.0, 31.0])

        self.assertEqual(len(stations), 2)
        self.assertEqual(stations[0]["name"], "Exxon")
        self.assertEqual(stations[0]["lat"], 31.0)
        self.assertEqual(stations[1]["name"], "Fuel station")
        self.assertEqual(stations[1]["lat"], 31.01)
        self.assertAlmostEqual(stations[1]["distance_meters"], 1112, delta=5)

    @patch("hos_planner.services.map_service.requests.post")
    def test_busy_server_raises_map_service_error(self, fake_post):
        fake_post.return_value = fake_ors_reply(429)

        with self.assertRaises(MapServiceError):
            map_service.search_fuel_stations([-100.0, 31.0])

    def test_query_uses_lat_then_lng(self):
        query = map_service.build_fuel_station_query([-100.5, 31.25])

        self.assertIn("around:5000,31.25,-100.5", query)


class FuelSearchFallbackTests(SimpleTestCase):
    @patch("hos_planner.planner.fuel_planner.search_fuel_stations", side_effect=MapServiceError())
    def test_search_failure_uses_the_road_point(self, fake_search):
        station = fuel_planner.find_fuel_station_near(new_state(), 100)

        self.assertEqual(station["name"], "Fuel stop")
        self.assertEqual(station["mile"], 100)
        self.assertEqual(fake_search.call_count, 1)


SEARCH_LOCATION_URL = "/api/search-location/"

FAKE_AUTOCOMPLETE_RESPONSE = {
    "features": [
        {"properties": {"label": "Indianapolis, IN, USA"}, "geometry": {"coordinates": [-86.14, 39.78]}},
    ]
}


class SearchLocationTests(APISimpleTestCase):
    @patch("hos_planner.services.map_service.requests.get")
    def test_returns_locations(self, fake_get):
        fake_get.return_value = fake_ors_reply(200, FAKE_AUTOCOMPLETE_RESPONSE)

        response = self.client.get(SEARCH_LOCATION_URL, {"text": "Indianap"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [{"name": "Indianapolis, IN, USA", "lng": -86.14, "lat": 39.78}])

    def test_text_too_short(self):
        response = self.client.get(SEARCH_LOCATION_URL, {"text": "In"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("text", response.data["error"]["details"])

    @patch("hos_planner.services.map_service.requests.get")
    def test_search_service_down(self, fake_get):
        fake_get.return_value = fake_ors_reply(503)

        response = self.client.get(SEARCH_LOCATION_URL, {"text": "Indianap"})

        self.assertEqual(response.status_code, 502)


REVERSE_LOCATION_URL = "/api/reverse-location/"


class ReverseLocationTests(APISimpleTestCase):
    @patch("hos_planner.services.map_service.requests.get")
    def test_returns_the_place_name_with_the_clicked_point(self, fake_get):
        fake_get.return_value = fake_ors_reply(200, {"features": [{"properties": {"label": "Joplin, MO, USA"}}]})

        response = self.client.get(REVERSE_LOCATION_URL, {"lat": 37.08, "lng": -94.51})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], {"name": "Joplin, MO, USA", "lat": 37.08, "lng": -94.51})

    @patch("hos_planner.services.map_service.requests.get")
    def test_no_place_found_uses_coordinates(self, fake_get):
        fake_get.return_value = fake_ors_reply(200, {"features": []})

        response = self.client.get(REVERSE_LOCATION_URL, {"lat": 37.08123, "lng": -94.51234})

        self.assertEqual(response.data["data"]["name"], "37.0812, -94.5123")

    def test_invalid_point(self):
        response = self.client.get(REVERSE_LOCATION_URL, {"lat": 120, "lng": -94.51})

        self.assertEqual(response.status_code, 400)
        self.assertIn("lat", response.data["error"]["details"])


class PlaceNameTests(SimpleTestCase):
    def setUp(self):
        map_service.find_place_name.cache_clear()

    @patch("hos_planner.services.map_service.requests.get")
    def test_town_and_state(self, fake_get):
        reply = {"features": [{"properties": {"locality": "Joplin", "region_a": "MO", "label": "Joplin, MO, USA"}}]}
        fake_get.return_value = fake_ors_reply(200, reply)

        self.assertEqual(map_service.find_place_name(37.08, -94.51), "Joplin, MO")

    @patch("hos_planner.services.map_service.requests.get")
    def test_county_when_no_town(self, fake_get):
        reply = {"features": [{"properties": {"county": "Quay County", "region_a": "NM"}}]}
        fake_get.return_value = fake_ors_reply(200, reply)

        self.assertEqual(map_service.find_place_name(35.1, -103.2), "Quay County, NM")

    @patch("hos_planner.services.map_service.requests.get")
    def test_same_point_is_looked_up_once(self, fake_get):
        reply = {"features": [{"properties": {"locality": "Joplin", "region_a": "MO"}}]}
        fake_get.return_value = fake_ors_reply(200, reply)

        map_service.find_place_name(37.08, -94.51)
        map_service.find_place_name(37.08, -94.51)

        self.assertEqual(fake_get.call_count, 1)

    @patch("hos_planner.planner.trip_handler.find_place_name", side_effect=MapServiceError())
    def test_failed_lookup_leaves_place_empty(self, fake_place_name):
        state = walk_state(100, 300, 20, [])
        planner.plan_drive(state)

        trip_handler.add_place_names(state)

        self.assertIsNone(state["segments"][0]["place"])

    @patch("hos_planner.planner.trip_handler.find_place_name", return_value="Joplin, MO")
    def test_places_reach_segments_stops_and_remarks(self, fake_place_name):
        state = walk_state(100, 1200, 20, [650])
        planner.plan_drive(state)

        trip_handler.add_place_names(state)
        logs = daily_logs.build_daily_logs(state)

        self.assertEqual(state["segments"][0]["place"], "Joplin, MO")
        self.assertEqual(state["stops"]["rest"][0]["place"], "Joplin, MO")
        self.assertEqual(logs[0]["remarks"][1]["place"], "Joplin, MO")
        self.assertLess(fake_place_name.call_count, len(state["segments"]))


class RemarkTests(SimpleTestCase):
    def test_no_remark_when_a_status_continues_past_midnight(self):
        logs = worked_example_logs()

        first_remark_day_2 = logs[1]["remarks"][0]
        self.assertEqual(first_remark_day_2["note"], "Pre-trip inspection")
        self.assertEqual(first_remark_day_2["time"], datetime(2026, 10, 2, 7, 30))

    def test_first_day_starts_with_off_duty_remark(self):
        logs = worked_example_logs()

        self.assertEqual(logs[0]["remarks"][0]["note"], "Off duty")
        self.assertEqual(logs[0]["remarks"][0]["time"], datetime(2026, 10, 1, 0, 0))


class FuelArrivalTests(SimpleTestCase):
    def test_fuel_stop_with_many_decimals_does_not_loop(self):
        state = walk_state(100, 1200, 20, [650.0000004])

        segments = planner.plan_drive(state)

        self.assertLess(len(segments), 40)
        fuel_start = state["stops"]["fuel"][0]["start"]
        self.assertEqual(fuel_start.replace(microsecond=0), datetime(2026, 10, 2, 10, 0))
