import json

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.status import HTTP_412_PRECONDITION_FAILED, HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS, HTTP_200_OK
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import detail_route, list_route
from django.db.models import Q, F
from django.db import connection

from .models import Channel, ChannelMembership
from .serializers import ReadChannelSerializer, CreateChannelSerializer
from .permissions import IsChannelTasksClosed, IsChannelOwner, IsChannelStillOpened, IsMemberStillExists, \
    HasFriendForPrivateChannel
from .signals import channel_ownership_changed, force_update_channel, kicked_member_from_channel
from doiq.tasks.serializers import TaskSerializer
from doiq.tasks.models import Task


class ChannelsViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ReadChannelSerializer
    authentication_classes = (JSONWebTokenAuthentication, )
    permission_classes = (
    IsAuthenticated, IsChannelTasksClosed, IsChannelOwner, IsChannelStillOpened, IsMemberStillExists,
    )#HasFriendForPrivateChannel
    lookup_field = 'channel_uid'

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'POST':
            return CreateChannelSerializer
        return ReadChannelSerializer

    def update(self, request, *args, **kwargs):
        if kwargs.get(self.lookup_field):
            channel = self.get_object()
            channel.opened = False
            channel.save()
            channel_data = self.serializer_class(channel)
            return Response(channel_data.data)

    def permission_denied(self, request, message=None):
        print dir(request), request.data, request.query_params, message
        reason = {'reason': message}
        if isinstance(message, tuple):
            if message[0] == 'tasks_not_closed':
                reason = {'reason': message[0]}
                tasks = TaskSerializer(message[1].channel_tasks.filter(~Q(status=3)), many=True)
                reason['tasks'] = JSONRenderer().render(tasks.data)
        reason = JSONRenderer().render(reason)
        permission_denied = PermissionDenied(reason)
        permission_denied.status_code = HTTP_412_PRECONDITION_FAILED
        raise permission_denied

    @detail_route(methods=['delete'])
    def kick_member(self, request, channel_uid):
        channel = self.get_object()
        member_id = request.GET.get('member_id')
        Task.objects.filter(related_channel=channel, assignee__id=member_id).update(assignee=F('owner'))
        membership = channel.channelmembership_set.get(member_id=member_id)
        membership.delete()
        kicked_member_from_channel.send(sender=ChannelMembership, membership=membership, owner=request.user)
        return Response(1)

    @detail_route(methods=['delete'])
    def change_owner(self, request, channel_uid):
        channel = self.get_object()
        member_id = request.GET.get('member_id')
        new_owner = request.user.__class__.objects.get(id=member_id)
        if not ChannelMembership.objects.filter(member=new_owner, channel=channel).count():
            ChannelMembership.objects.create(member=new_owner, channel=channel)
        channel.owner = new_owner
        channel.save()
        channel_ownership_changed.send(sender=channel.__class__,
                                       channel=channel,
                                       owner=request.user,
                                       new_owner=new_owner
                                       )
        return Response(1)

    @list_route(methods=['put'])
    def private_channel(self, request, channel_uid=None):
        friend_id = request.GET.get('friend_id')
        action = request.GET.get('action')
        friend = request.user.__class__.objects.get(id=friend_id)
        cursor = connection.cursor()
        cursor.execute('SELECT c.channel_uid FROM channel_channel c '
                       'JOIN channel_channelmembership cm1 ON c.id = cm1.channel_id AND cm1.member_id = %s'
                       'JOIN channel_channelmembership cm2 ON c.id = cm2.channel_id AND cm2.member_id = %s'
                       'WHERE c.type = 1',
                       (friend.id, request.user.id)
                       )
        private_channel_uid = cursor.fetchone()
        if action == 'open':
            if not private_channel_uid:
                private_channel = Channel.objects.create(
                    type=1,
                    name='-'.join((friend.username, request.user.username)),
                    owner=request.user
                )
                ChannelMembership.objects.bulk_create(
                    [
                        ChannelMembership(member=friend, channel=private_channel),
                        ChannelMembership(member=request.user, channel=private_channel, private_channel_opened=True)
                    ]
                )
            else:
                private_channel_uid = private_channel_uid[0]
                private_channel = Channel.objects.get(channel_uid=private_channel_uid)
                ChannelMembership.objects.filter(member=request.user, channel=private_channel).update(
                    private_channel_opened=True)
            force_update_channel.send(sender=ChannelMembership, channel=private_channel, user=friend)
            serialized_data = ReadChannelSerializer(private_channel).data
        elif action == 'close':
            if not private_channel_uid:
                return Response({'reason': 'no_open_private_chat'}, status=HTTP_412_PRECONDITION_FAILED)
            private_channel_uid = private_channel_uid[0]
            private_channel = Channel.objects.get(channel_uid=private_channel_uid)
            ChannelMembership.objects.filter(member=request.user, channel=private_channel).update(
                    private_channel_opened=False)
            serialized_data = ReadChannelSerializer(private_channel).data
        return Response(serialized_data)
