"""{{ project_name }} URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/{{ docs_version }}/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import importlib

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from django.urls import include, path

from rest_framework.authtoken.views import obtain_auth_token

from huscy_project.views import (
    health_check,
    ListInstalledHuscyAppsView,
    LoginAPIView,
    LogoutAPIView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', LoginView.as_view(template_name='admin/login.html')),
    path('', TemplateView.as_view(template_name='index.html')),
    path('health_check/', health_check),
    path('api-auth-token/', obtain_auth_token),
    path('api-login/', LoginAPIView.as_view()),
    path('api-logout/', LogoutAPIView.as_view()),
    path('installed_huscy_apps/', ListInstalledHuscyAppsView.as_view()),
]

if settings.DEBUG:
    urlpatterns.append(
        path('api-auth/', include('rest_framework.urls')),
    )

for app in apps.get_app_configs():
    if hasattr(app, 'HuscyAppMeta'):
        try:
            importlib.import_module(f'{app.name}.urls')
            urlpatterns.append(path('', include(f'{app.name}.urls')))
        except ImportError:
            pass
