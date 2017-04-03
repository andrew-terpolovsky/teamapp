from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.SimpleRouter()
router.register(r'channels', views.ChannelsViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
