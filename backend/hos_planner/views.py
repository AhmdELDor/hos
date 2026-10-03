from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError

from hos_planner.api.responses import success_response
from hos_planner.api.serializers import DriverRequestSerializer, LocationSerializer
from hos_planner.planner.trip_handler import plan_trip
from hos_planner.services.map_service import reverse_location, search_locations


@api_view(["POST"])
def plan_drive(request):
    serializer = DriverRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    driver_request = serializer.validated_data
    trip = plan_trip(driver_request)

    return success_response(trip)


@api_view(["GET"])
def search_location(request):
    text = request.query_params.get("text", "").strip()

    if len(text) < 3:
        raise ValidationError({"text": ["Type at least 3 characters."]})

    locations = search_locations(text)

    return success_response(locations)


@api_view(["GET"])
def reverse_location_view(request):
    serializer = LocationSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    point = serializer.validated_data
    location = reverse_location(point["lat"], point["lng"])

    return success_response(location)
