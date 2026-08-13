from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InspectionViewSet, InspectionRecordViewSet, WorkOrderViewSet

router = DefaultRouter()
router.register(r'inspections', InspectionViewSet, basename='inspection')
router.register(r'records', InspectionRecordViewSet, basename='inspection-record')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')

urlpatterns = [
    path('', include(router.urls)),
]
