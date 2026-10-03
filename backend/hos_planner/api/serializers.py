from rest_framework import serializers

from hos_planner import constants


class LocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)
    name = serializers.CharField(required=False, allow_blank=True, max_length=200)


class DriverRequestSerializer(serializers.Serializer):
    current_location = LocationSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    cycle_used = serializers.FloatField(min_value=0, max_value=constants.MAX_CYCLE_HOURS)

    def validate(self, data):
        pickup = data["pickup_location"]
        dropoff = data["dropoff_location"]

        if pickup["lat"] == dropoff["lat"] and pickup["lng"] == dropoff["lng"]:
            raise serializers.ValidationError("Pickup and dropoff must be different locations.")

        return data
