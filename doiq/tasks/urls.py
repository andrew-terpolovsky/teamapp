from django.conf.urls import url, include
from doiq.tasks import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'tasks', views.TaskViewSet)
router.register(r'activity', views.ActivityViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
