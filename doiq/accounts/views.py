import calendar
from urlparse import urljoin

import pytz
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from doiq.accounts import serializers as serializer
from doiq.accounts.models import User, Invite
from doiq.channel.models import ChannelMembership
from doiq.channel.serializers import ReadChannelSerializer
from doiq.utils.mail import send_email
from rest_framework import status
from rest_framework.decorators import permission_classes, authentication_classes, api_view, renderer_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from rest_framework_jwt.settings import api_settings
from datetime import datetime

class Request_(object):
    pass

@api_view(['POST'])
@permission_classes((AllowAny,))
def registration(request):
    serialized = serializer.RegistrationSerializer(data=request.data)
    if serialized.is_valid():
        invite_id = request.data.pop('invite_id', None)
        user = User.objects.create_user(**serialized.data)
        if invite_id:
            invite = Invite.objects.filter(pk=invite_id)
            if invite.count():
                invite = invite[0]
                invite.user = user
                invite.accepted = True
                invite.save()

                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                payload = jwt_payload_handler(user)

                if api_settings.JWT_ALLOW_REFRESH:
                    payload['orig_iat'] = calendar.timegm(
                        datetime.utcnow().utctimetuple()
                    )
                jwt_token = jwt_encode_handler(payload)
                response = {'invited': True, 'jwt_token': jwt_token}
                if invite.channel:
                    response.update({'channel': invite.channel.channel_uid})
                unaccepted_invites = Invite.objects.filter(email=user.email, accepted=False)
                for i in unaccepted_invites:
                    i.user = user
                    i.accepted = True
                    i.save()
                return Response(response, status=status.HTTP_201_CREATED)
        else:
            user.is_active = False
            user.save()

            t = calendar.timegm(user.date_joined.timetuple())
            token = urlsafe_base64_encode('{0}:do-iq-app:{1}'.format(
                user.email, t))

            context = {
                'user': user,
                'url': urljoin(
                    settings.HOSTNAME,
                    reverse('accounts:activate', kwargs={'token': token})),
            }

            send_email(
                subject='Email Confirmation',
                email=user.email,
                template='emails/accounts/email_confirmation.html',
                context=context
            )

            unaccepted_invites = Invite.objects.filter(email=user.email, accepted=False)
            for i in unaccepted_invites:
                i.user = user
                i.accepted = True
                i.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def reset_password(request):
    serialized = serializer.ResetPasswordSerializer(data=request.data)
    if serialized.is_valid():
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes((AllowAny,))
@renderer_classes((JSONRenderer,))
def activate(request, token):
    if request.method == 'POST':
        result = urlsafe_base64_decode(token).split(":")
        user = User.objects.get(email=result[0])
        try:
            date = datetime.utcfromtimestamp(float(result[2]))
            datetime_income = pytz.UTC.localize(date)
            datetime_user = user.date_joined.replace(microsecond=0)
            if datetime_income != datetime_user:
                raise User.DoesNotExist
        except User.DoesNotExist or IndexError or ValueError:
            pass
            # messages.error(
            #     request, message='Activation url is invalid', extra_tags='error')
        else:
            if not user.is_active:
                user.is_active = True
                user.save()

            # messages.success(request, message='Activation complete',
            #                  extra_tags='success')

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)

        if api_settings.JWT_ALLOW_REFRESH:
            payload['orig_iat'] = calendar.timegm(
                datetime.utcnow().utctimetuple()
            )
        jwt_token = jwt_encode_handler(payload)
        data = {}
        data['jwt_token'] = jwt_token
        return Response(data)
    return redirect('/activate/{token}/'.format(token=token))


@api_view(['POST'])
@authentication_classes((JSONWebTokenAuthentication,))
@permission_classes((IsAuthenticated,))
def logout(request):
    pass


@api_view(['GET', 'POST'])
@permission_classes((AllowAny,))
def accept_invite(request, signature=None):
    if request.method == 'POST':
        data = Invite.verify_signature(signature)
        if data.get('pk'):
            invite = Invite.objects.get(pk=data.get('pk'))
            if invite.user:
                invite.accepted = True
                invite.save()
                jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                payload = jwt_payload_handler(invite.user)

                if api_settings.JWT_ALLOW_REFRESH:
                    payload['orig_iat'] = calendar.timegm(
                        datetime.utcnow().utctimetuple()
                    )
                jwt_token = jwt_encode_handler(payload)
                data['jwt_token'] = jwt_token
                if invite.channel:
                    data['channel'] = ReadChannelSerializer(invite.channel).data
                _request = Request_()
                setattr(_request, 'user', invite.user)
                data['friend'] = serializer.FriendsAccountSerializer(
                    invite.invited_by,
                    context={'request': _request}
                ).data
        return Response(data)
    return redirect('/sign-up/{token}/'.format(token=signature))