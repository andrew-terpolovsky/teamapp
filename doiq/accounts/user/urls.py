from rest_framework import routers
from .views import AccountsViewSet, FriendsViewSet

router = routers.SimpleRouter()
router.register(r'accounts', AccountsViewSet)
router.register(r'friends', FriendsViewSet)
