from rest_framework import serializers
from .models import MeasureStation, WaterMeasurement, WaterAlarm


class MeasureStationSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = MeasureStation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_data_time']


class WaterMeasurementSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)

    class Meta:
        model = WaterMeasurement
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterAlarmSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.real_name', read_only=True)

    class Meta:
        model = WaterAlarm
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
