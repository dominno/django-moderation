try:
    from django.conf.urls.defaults import patterns, include, handler500
except ImportError:
    from django.conf.urls import patterns, include, handler500
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

handler500

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}),
)
