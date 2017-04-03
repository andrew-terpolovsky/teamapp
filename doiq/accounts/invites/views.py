from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from rest_framework import status, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from doiq.accounts import serializers as serializer
from doiq.accounts.models import Invite
from doiq.channel.models import Channel, ChannelMembership
from doiq.chat.models import Chat
from doiq.chat.serializers import ChatSerializer
from doiq.channel.signals import friend_added_to_channel


User = get_user_model()


class InvitesViewSet(viewsets.ModelViewSet):
    queryset = Invite.objects.all()
    serializer_class = serializer.InviteSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_queryset(self):
        by = self.request.GET.get('by', 'created')
        return self.queryset.filter(invited_by=self.request.user).order_by(by)

    def list(self, request, *args, **kwargs):
        distinct_invitation = self.get_queryset().distinct('email').order_by('email')
        serialized_data = self.get_serializer_class()(distinct_invitation, context={'request': request}, many=True).data
        # json_data = JSONRenderer().render(serialized_data)
        return Response(serialized_data)

    # def get_object(self):

    @list_route(["POST"])
    def send(self, request):
        try:
            data = JSONParser().parse(request)
            emails = data.get('emails', [])
            channel = data.get('channel')
            if channel:
                try:
                    channel = Channel.objects.get(pk=channel)
                    if channel.owner != request.user:
                        raise Exception('Only channel owner is able to send invitations.')
                except Channel.DoesNotExist:
                    channel = None
            emails_sent = 0
            flag_invite_yourself = False
            flag_invite_already_friend = 0
            flag_invite_already_exists = False
            have_friendship_already = set(request.user.friends.values_list('email', flat=True))
            friend_ids = data.get('ids')
            for email in emails:
                email = email['text'].strip()
                validate_email(email)
                if email:
                    if request.user.email == email:
                        flag_invite_yourself = True
                        continue
                    if email in have_friendship_already and not channel:
                        flag_invite_already_friend += 1
                        continue
                    elif email in have_friendship_already and channel:
                        if Invite.objects.filter(
                                invited_by=self.request.user,
                                email=email,
                                accepted=False,
                                channel=channel).count():
                            flag_invite_already_exists = True
                            continue
                        if ChannelMembership.objects.filter(channel=channel,
                                                            member__email=email).count():
                            flag_invite_already_friend += 1
                            continue
                    user = User.objects.filter(email=email).first()
                    invite, created = Invite.objects.get_or_create(
                        invited_by=self.request.user,
                        email=email,
                        accepted=False,
                        channel=channel,
                        user=user
                    )
                    if not created:
                        flag_invite_already_exists = True
                        continue
                    invite.save()
                    invite.send_invite_email(request)
                    emails_sent += 1

            new_members = []
            if channel:
                existing_channel_members = ChannelMembership.objects.filter(channel=channel,
                                                                            member__id__in=friend_ids).values_list(
                    'member__id', flat=True)
                non_existing_channel_members = set(friend_ids).difference(set(existing_channel_members))
                for m in non_existing_channel_members:
                    template = u'{user} have joined the channel.'.format(user=User.objects.get(id=m).username)
                    message = Chat.objects.create(sender=request.user, message=template, channel=channel, type=3)
                    serialized_message = ChatSerializer(message).data
                    cm = ChannelMembership(channel=channel, member_id=m)
                    cm._message = serialized_message
                    cm.save()
                    new_members.append(m)
                    Invite.send_notification_invited_to_channel_email(cm.member, channel, request.user)
                    friend_added_to_channel.send(sender=channel.__class__,
                                                 channel=channel,
                                                 friend=cm.member,
                                                 inviter=request.user
                                                 )

            return Response({
                'success': True,
                'emails_sent': emails_sent,
                'new_members': new_members,
                'flag_invite_yourself': flag_invite_yourself,
                'flag_invite_already_friend': flag_invite_already_friend,
                'flag_invite_already_exists': flag_invite_already_exists,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'errors': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @detail_route(['PUT'])
    def resend(self, request, pk=None):
        try:
            invite = self.get_object()
            invite.send_invite_email(request)
            serialized = self.serializer_class(invite, context={'request': request})
            return Response(serialized.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
