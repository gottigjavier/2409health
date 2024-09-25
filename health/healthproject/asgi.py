"""
ASGI config for healthproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthproject.settings')

asgi_application = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.urls import path
from nursing import consumer

websocket_urlPattern = [
    path('ws/appData/', consumer.appConsumer.as_asgi()),
    path('ws/callData/', consumer.callConsumer.as_asgi()),
    path('ws/taskData/', consumer.taskConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': asgi_application,
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlPattern))
})