"""
URL configuration for AI Novel Factory.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from novels.admin_views import get_custom_admin_urls

# Custom admin pipeline URLs — must be before the main admin/ to be reachable
custom_admin_patterns = get_custom_admin_urls()

urlpatterns = [
    # Custom admin pipeline views (no namespace to avoid conflict)
    path('admin/', include(custom_admin_patterns)),

    # Standard Django admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include('novels.api.urls')),

    # DRF Auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

