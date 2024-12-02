"""
URL configuration for HeroHoursRemake project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, include


def home(request):
    return HttpResponse("Hello, world!")
def favicon(request):
    return HttpResponse(status=204)
def root_redirect(request):
    return redirect('/HeroHours/')
urlpatterns = [
    path('HeroHours/', include('HeroHours.urls')),
    path('api/', include('HeroHours_api.urls')),
    path('favicon.ico', favicon),
    path('admin/', admin.site.urls),
    path('test/', home),
    path('', root_redirect),
]
