from rest_framework import serializers
from .models import IrrigationDevice, IrrigationLog, IrrigationPlan, IrrigationRecord


class IrrigationDeviceSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = IrrigationDevice
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_heartbeat']


class IrrigationLogSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    operator_name = serializers.CharField(source='operator.real_name', read_only=True)

    class Meta:
        model = IrrigationLog
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class IrrigationPlanSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)
    device_names = serializers.SerializerMethodField()

    class Meta:
        model = IrrigationPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def get_device_names(self, obj):
        return [d.name for d in obj.devices.all()]


class IrrigationRecordSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = IrrigationRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
