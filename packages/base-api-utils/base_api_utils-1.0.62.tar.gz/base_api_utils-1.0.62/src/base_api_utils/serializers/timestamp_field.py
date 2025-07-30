from datetime import timezone, datetime

from rest_framework import serializers
import time


class TimestampField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return datetime.fromtimestamp(int(data), tz=timezone.utc)
        except (ValueError, OSError):
            raise serializers.ValidationError("Invalid timestamp format.")

    def to_representation(self, value):
        return int(time.mktime(value.timetuple()))