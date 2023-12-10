"""
ASGI config for Bangla project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Bangla.settings')

django_asgi = get_asgi_application()

from ads import urls
from matrimonials import urls as mu

application = ProtocolTypeRouter(
    {
        "http": django_asgi,
        "websocket": URLRouter(urls.websocket_urlpatterns + mu.websocket_urlpatterns)
    }
)
