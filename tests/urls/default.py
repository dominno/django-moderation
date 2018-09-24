from __future__ import unicode_literals
from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
