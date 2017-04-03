from rest_framework import routers
from .views import InvitesViewSet

router = routers.SimpleRouter()
router.register(r'invites', InvitesViewSet)
