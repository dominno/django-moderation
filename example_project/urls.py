from django.conf import settings
from django.conf.urls import handler500, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

from moderation.helpers import auto_discover

admin.autodiscover()
auto_discover()

handler500  # Pyflakes

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/$', auth_views.LoginView.as_view()),
]

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
    urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
