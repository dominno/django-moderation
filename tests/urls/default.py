from django.conf import settings
from django.contrib import admin

try:
    from django.urls import path

    admin_path = path('admin/', admin.site.urls)
except ImportError:
    from django.conf.urls import include, url

    admin_path = url(r'^admin/', include(admin.site.urls))
from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = [
    admin_path,
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
