from django.conf.urls import url, include
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from .invites.urls import router as invite_router
from .user.urls import router as user_router
from .user.views import CurrentUser
from .views import registration, reset_password, activate, accept_invite

urlpatterns = [
    url(
        regex=r'^token-auth/$',
        view=obtain_jwt_token,
        name="token_auth"
    ),
    url(
        regex=r'^logout/$',
        view=refresh_jwt_token,
        name="logout"
    ),
    url(
        regex=r'^registration/$',
        view=registration,
        name="sign_up"
    ),
    url(
        regex=r'^reset-password/$',
        view=reset_password,
        name='reset_password'
    ),
    url(
        regex=r'^activate/(?P<token>[0-9A-Za-z_\-]+)/$',
        view=activate,
        name='activate'
    ),
    url(
        regex=r'^accept-invite/(?P<signature>.+)/$',
        view=accept_invite,
        name='accept_invite'
    ),
    url(
        regex=r'^complete-sign-up/(?P<token>.+)/$',
        view=activate,
        name='complete_sign_up'
    ),
    url(
        regex=r'^me/$',
        view=CurrentUser.as_view(),
        kwargs={'pk': 1},
        name='me'
    ),
    url(r'^', include(user_router.urls)),
    url(r'^', include(invite_router.urls)),
]
