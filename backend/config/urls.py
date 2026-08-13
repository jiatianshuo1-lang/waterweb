from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.users.views import AuthViewSet

auth_viewset = AuthViewSet.as_view({'post': 'login'})

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/auth/login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('api/v1/auth/register/', AuthViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('api/v1/auth/me/', AuthViewSet.as_view({'get': 'me'}), name='auth-me'),
    path('api/v1/auth/refresh/', AuthViewSet.as_view({'post': 'refresh'}), name='auth-refresh'),
    path('api/v1/auth/verify/', AuthViewSet.as_view({'post': 'verify'}), name='auth-verify'),
    path('api/v1/auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
    path('api/v1/auth/change-password/', AuthViewSet.as_view({'post': 'change_password'}), name='auth-change-password'),

    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/common/', include('apps.common.urls')),
    path('api/v1/inspection/', include('apps.inspection.urls')),
    path('api/v1/water-measurement/', include('apps.water_measurement.urls')),
    path('api/v1/smart-irrigation/', include('apps.smart_irrigation.urls')),
    path('api/v1/water-allocation/', include('apps.water_allocation.urls')),
    path('api/v1/water-price/', include('apps.water_price.urls')),
    path('api/v1/daily/', include('apps.daily_management.urls')),
    path('api/v1/soil-weather/', include('apps.soil_weather.urls')),
    path('api/v1/ai/', include('apps.ai_assistant.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = '灌区管理系统'
admin.site.site_title = '灌区管理系统后台'
admin.site.index_title = '欢迎使用灌区管理系统'
