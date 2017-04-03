from django.db.models import Q
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from .models import User
from .serializers import AccountSerializer, FriendsSerializer
from doiq.channel.models import Channel


class CurrentUser(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = AccountSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):

        action = request.GET.get('action')
        if action == 'friend_delete':
            friend_id = request.GET.get('friend_id')
            if friend_id:
                request.user.friends.remove(friend_id)
        return Response(self.get_serializer_class()(request.user).data)


class AccountsViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AccountSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class FriendsViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = FriendsSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        channel_uid = self.request.GET.get('channel')
        if channel_uid:
            channel = Channel.objects.get(channel_uid=channel_uid)
            return channel.members

        ids = list(self.request.user.friends.filter(username__icontains=query).values_list('id', flat=True))
        ids.append(self.request.user.id)
        return self.queryset.filter(pk__in=ids)
