from rest_framework.permissions import BasePermission
from django.db.models import Q


class IsChannelTasksClosed(BasePermission):
    message = 'tasks_not_closed'

    def has_object_permission(self, request, view, obj):
        action = request.GET.get('action')
        if request.method == 'PUT' and action == 'archive':
            if obj.channel_tasks.filter(~Q(status=3)).count():
                self.message = (self.message, obj)
                return False
        return super(IsChannelTasksClosed, self).has_object_permission(request, view, obj)


class IsChannelOwner(BasePermission):
    message = 'not_owner'

    def has_object_permission(self, request, view, obj):
        action = request.GET.get('action')
        if (request.method == 'PUT' and action == 'archive') or \
                (request.method == 'DELETE' and 'kick_member' in request.path.split('/')) or \
                (request.method == 'DELETE' and 'change_owner' in request.path.split('/')):
            if not obj.owner == request.user:
                return False
        return super(IsChannelOwner, self).has_object_permission(request, view, obj)


class IsChannelStillOpened(BasePermission):
    message = 'not_opened'

    def has_object_permission(self, request, view, obj):
        action = request.GET.get('action')
        if request.method == 'PUT' and action == 'archive':
            if not obj.opened:
                return False
        return super(IsChannelStillOpened, self).has_object_permission(request, view, obj)

class IsMemberStillExists(BasePermission):
    message = 'not_existing_member'

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE' and 'kick_member' in request.path.split('/'):
            member_id = request.GET.get('member_id')
            if not obj.channelmembership_set.filter(member_id=member_id).count():
                return False
        return super(IsMemberStillExists, self).has_object_permission(request, view, obj)

class HasFriendForPrivateChannel(BasePermission):
    message = 'not_existing_friend'

    def has_permission(self, request, view):

        if request.method == 'PUT' and 'private_channel' in request.path.split('/'):
            action = request.GET.get('action')
            friend_id = request.GET.get('friend_id')
            if action == 'open':
                if not request.user.friends.filter(id=friend_id).count():
                    return False
        return super(HasFriendForPrivateChannel, self).has_permission(request, view)