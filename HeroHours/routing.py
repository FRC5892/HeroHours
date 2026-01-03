from django.urls import path

from HeroHours.consumers import LiveConsumer

websocket_urlpatterns = [
    path('ws/live/',LiveConsumer.as_asgi()),
]
