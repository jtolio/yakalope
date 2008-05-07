from django.conf.urls.defaults import *
from yakalope.views import login
from yakalope.views import search
from yakalope.views import recent
from yakalope.views import logout

urlpatterns = patterns('',
    # Example:
    # (r'^server/', include('server.foo.urls')),

    (r'^login$', login),
    (r'^search$', search),
    (r'^recent$', recent),
    (r'^logout$', logout),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),
)
