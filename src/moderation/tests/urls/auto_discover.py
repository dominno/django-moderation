from django.conf.urls.defaults import patterns, include, handler500
from django.conf import settings
from django.contrib import admin
from moderation.helpers import auto_discover

admin.autodiscover()
auto_discover()

handler500

urlpatterns = patterns(
    '',
        (r'^admin/', include(admin.site.urls)),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
             {'document_root': settings.MEDIA_ROOT}),
    )
