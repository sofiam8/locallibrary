"""
URL configuration for locallibrary_config project.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from .api import api
from taskflow.api import api as taskflow_api, api_v2 as taskflow_api_v2

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('catalog/', include('catalog.urls')),
    path('chat/', include('chat.urls')),
    path('', RedirectView.as_view(url='catalog/')),
    path("api/", api.urls),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    path("taskflow/api/v2/", taskflow_api_v2.urls),
    path("taskflow/api/", taskflow_api.urls),
]
