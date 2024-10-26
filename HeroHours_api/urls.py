from django.urls import path

from HeroHours_api import views
from .views import (
    TodoListApiView,
)
urlpatterns = [
    path('', TodoListApiView.as_view(), name='index'),

]