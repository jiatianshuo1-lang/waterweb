from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WaterPricePolicyViewSet, WaterUserViewSet, WaterBillViewSet, WaterPaymentViewSet

router = DefaultRouter()
router.register(r'policies', WaterPricePolicyViewSet, basename='water-price-policy')
router.register(r'users', WaterUserViewSet, basename='water-user')
router.register(r'bills', WaterBillViewSet, basename='water-bill')
router.register(r'payments', WaterPaymentViewSet, basename='water-payment')

urlpatterns = [
    path('', include(router.urls)),
]
