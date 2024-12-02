from django.urls import path, re_path

from HeroHours_api import views
from .views import (
    SheetPullAPI,
    MeetingPullAPI
)
urlpatterns = [
    path('sheet/users/', SheetPullAPI.as_view(), name='sheet'),
    path('sheet/<int:year>/<int:month>/<int:day>/', MeetingPullAPI.as_view(),name='sheet meeting')
]