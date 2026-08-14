from rest_framework import serializers
from .models import RegionModel, CommonConfig


class RegionSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = RegionModel
        fields = [
            'id', 'code', 'name', 'region_type', 'parent', 'parent_name',
            'geometry', 'description', 'sort_order', 'children'
        ]

    def get_children(self, obj):
        if hasattr(obj, 'children') and obj.children.exists():
            return RegionSerializer(obj.children.all(), many=True, context=self.context).data
        return []


class CommonConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonConfig
        fields = ['id', 'config_type', 'config_key', 'config_value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
