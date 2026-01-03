"""
ASGI config for HeroHoursRemake project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HeroHoursRemake.settings")

django_asgi_app = get_asgi_application()

import HeroHours.routing

application = ProtocolTypeRouter({
    "websocket": AllowedHostsOriginValidator(AuthMiddlewareStack(
        URLRouter(HeroHours.routing.websocket_urlpatterns),
    )),
    "http": django_asgi_app,
})