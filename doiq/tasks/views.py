from django.db.models import Q
from doiq.tasks.models import Task, Activity
from doiq.tasks.serializers import TaskSerializer, ActivitySerializer
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_queryset(self):
        by = [self.request.GET.get('by', '-id')]
        if by[0] == 'assignee__full_name':
            by.append('assignee__username')

        channel = self.request.GET.get('channel')
        archived = self.request.GET.get('archived')
        my_channel_tasks = self.request.GET.get('my_channel_tasks')
        private = self.request.GET.get('private')
        queryset = self.queryset.filter(deleted=False)

        if channel:
            queryset = queryset.filter(related_channel_id=channel)

        elif archived:
            ids = self.request.user.channels.all().values_list('id', flat=True)
            queryset = self.queryset.filter(
                Q(related_channel_id__in=ids) | Q(owner=self.request.user) | Q(assignee=self.request.user),
                Q(deleted=True)
            )

        elif my_channel_tasks:
            ids = self.request.user.channels.all().values_list('id', flat=True)
            queryset = queryset.filter(related_channel_id__in=ids)

        elif private:
            # ids = self.request.user.channels.all().values_list('id', flat=True)
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(assignee=self.request.user)# | Q(related_channel_id__in=ids)
            )

        return queryset.order_by(*by)

    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        if request.user == task.owner:
            task.deleted = True
            task.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.filter(deleted=False)
    serializer_class = ActivitySerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_queryset(self):
        task = self.request.GET.get('task')
        if task:
            return self.queryset.filter(task_id=task)
        else:
            return self.queryset

    def destroy(self, request, *args, **kwargs):
        activity = self.get_object()
        if request.user == activity.sender and not activity.system and not activity.task.deleted:
            activity.deleted = True
            activity.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_403_FORBIDDEN)
