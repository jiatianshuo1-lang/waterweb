from rest_framework import serializers
from .models import Inspection, WorkOrder, WorkOrderLog, InspectionRecord


class InspectionRecordSerializer(serializers.ModelSerializer):
    inspector_name = serializers.CharField(source='inspector.real_name', read_only=True)

    class Meta:
        model = InspectionRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class InspectionSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    inspector_names = serializers.SerializerMethodField()

    class Meta:
        model = Inspection
        fields = [
            'id', 'code', 'title', 'template_type', 'priority', 'region', 'region_name',
            'inspectors', 'inspector_names', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
            'status', 'description', 'checklist', 'photos', 'report', 'result',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_inspector_names(self, obj):
        return [u.real_name or u.username for u in obj.inspectors.all()]


class InspectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = [
            'title', 'template_type', 'priority', 'region', 'inspectors',
            'planned_start', 'planned_end', 'description', 'checklist'
        ]


class InspectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspection
        fields = [
            'title', 'template_type', 'priority', 'region', 'inspectors',
            'planned_start', 'planned_end', 'status', 'description', 'checklist',
            'photos', 'report', 'result', 'actual_start', 'actual_end'
        ]


class WorkOrderLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.real_name', read_only=True)

    class Meta:
        model = WorkOrderLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class WorkOrderSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    reporter_name = serializers.CharField(source='reporter.real_name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.real_name', read_only=True)
    verifier_name = serializers.CharField(source='verifier.real_name', read_only=True)
    logs = WorkOrderLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'code', 'title', 'order_type', 'priority', 'status',
            'region', 'region_name', 'inspection',
            'reporter', 'reporter_name', 'assignee', 'assignee_name',
            'verifier', 'verifier_name', 'description', 'location', 'contact_info',
            'photos', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
            'solution', 'cost', 'result_photos', 'satisfaction', 'logs',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class WorkOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = [
            'title', 'order_type', 'priority', 'region', 'inspection',
            'description', 'location', 'contact_info', 'photos'
        ]


class WorkOrderAssignSerializer(serializers.Serializer):
    assignee = serializers.IntegerField()
    planned_start = serializers.DateTimeField(required=False)
    planned_end = serializers.DateTimeField(required=False)
    remark = serializers.CharField(required=False)


class WorkOrderCompleteSerializer(serializers.Serializer):
    solution = serializers.CharField()
    actual_end = serializers.DateTimeField(required=False)
    cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    result_photos = serializers.ListField(child=serializers.CharField(), required=False)
    remark = serializers.CharField(required=False)


class WorkOrderVerifySerializer(serializers.Serializer):
    satisfied = serializers.BooleanField(default=True)
    satisfaction = serializers.IntegerField(min_value=1, max_value=5, required=False)
    remark = serializers.CharField(required=False)
