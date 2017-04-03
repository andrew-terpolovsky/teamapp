from django.conf.urls import url
from .views import get_timezones, upload

urlpatterns = [
    url(r'^get-timezones/$', get_timezones, name='get_timezones'),
    url(r'^upload/$', upload, name='upload'),
]
