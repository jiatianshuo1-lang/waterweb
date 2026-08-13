from rest_framework import serializers
from .models import WaterSource, WaterAllocation, WaterAllocationDetail, WaterTransfer


class WaterSourceSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = WaterSource
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WaterAllocationDetailSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = WaterAllocationDetail
        fields = '__all__'


class WaterAllocationSerializer(serializers.ModelSerializer):
    details = WaterAllocationDetailSerializer(many=True, required=False)
    source_name = serializers.CharField(source='water_source.name', read_only=True)

    class Meta:
        model = WaterAllocation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        allocation = WaterAllocation.objects.create(**validated_data)
        self._save_details(allocation, details_data)
        return allocation

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if details_data is not None:
            instance.details.all().delete()
            self._save_details(instance, details_data)
        return instance

    def _save_details(self, allocation, details_data):
        total = sum(d['allocated_amount'] for d in details_data) if details_data else 1
        for d in details_data:
            d['ratio'] = round(d['allocated_amount'] / total * 100, 2) if total > 0 else 0
            d['surplus'] = d['allocated_amount']
            WaterAllocationDetail.objects.create(allocation=allocation, **d)


class WaterTransferSerializer(serializers.ModelSerializer):
    from_region_name = serializers.CharField(source='from_region.name', read_only=True)
    to_region_name = serializers.CharField(source='to_region.name', read_only=True)

    class Meta:
        model = WaterTransfer
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
