import os
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.conf.urls.static import static



from apps.ghtracker.views import IndexView

urlpatterns = patterns('',
    # Homepage
    url(r'^$', IndexView.as_view(), name='home'),
)

#used to show static assets out of the collected-static
if getattr(settings, 'SERVE_STATIC', False) and settings.SERVE_STATIC:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': False,}),
        url(r'^uploads/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False,}),
    )
