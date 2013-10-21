
from django.conf.urls.defaults import patterns, include, handler500, url
from django.conf import settings
from django.contrib import admin
from moderation.helpers import auto_discover
admin.autodiscover()
auto_discover()

handler500 # Pyflakes

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )

    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_ROOT}),
    )