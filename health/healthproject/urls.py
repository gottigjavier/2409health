"""healthproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import include, path, re_path
from . import settings
from django.views.static import serve
from nursing.api import api as nursing_api
from nursing.api import django_register

static_urlpatterns = [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {"document_root": settings.REACT_BUILD_DIR + "/static"},
    ),
    re_path(
        r"^$", serve, {"document_root": settings.REACT_BUILD_DIR, "path": "index.html"}
    ),
    re_path(
        r"^(?!static|media|api|admin).*$",
        serve,
        {"document_root": settings.REACT_BUILD_DIR, "path": "index.html"},
    ),
]


urlpatterns = [
    path("admin/", admin.site.urls),
    # Override Ninja register endpoint with a fallback Django view that
    # accepts raw JSON/form payloads in case the Ninja parser doesn't see
    # the body (some middleware can consume the stream). This entry is
    # intentionally placed before the `api/` include so it takes precedence.
    path("api/auth/register", django_register),
    path("api/", nursing_api.urls),
    path("nursing/", include("nursing.urls")),
    path("", include(static_urlpatterns)),
]
