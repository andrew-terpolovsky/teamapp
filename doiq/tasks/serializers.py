from django.conf import settings
from doiq.accounts.models import User
from doiq.accounts.serializers import FriendsSerializer
from doiq.filemanager.models import FileManager
from doiq.filemanager.serializers import FileManagerSerializer
from doiq.tasks.models import Task, Activity
from rest_framework import serializers


class TaskSerializer(serializers.ModelSerializer):
    assignee = FriendsSerializer(many=False, read_only=True)
    files = FileManagerSerializer(many=True, read_only=True)
    owner = FriendsSerializer(many=False, read_only=True)
    get_priority_display = serializers.ReadOnlyField()
    get_status_display = serializers.ReadOnlyField()
    due_date = serializers.DateField(required=True, input_formats=[settings.DATE_TIME_FORMAT, settings.DATE_FORMAT])

    def create(self, validated_data):
        request = self.context['request']
        assignee = None

        if 'assignee' in request.data:
            assignee = request.data['assignee'].get('id')

        task = Task.objects.create(assignee_id=assignee, owner=request.user, **validated_data)

        if 'files' in request.data:
            files = map(lambda f: f.get('id'), request.data['files'])
            task.files.add(*files)

        Activity.objects.create(
            system=True,
            template_id='task_created',
            task=task,
            sender=request.user
        )

        return task

    def update(self, instance, validated_data):
        request = self.context['request']
        activity_list = []

        if 'assignee' in request.data and request.data['assignee']:
            a_id = request.data['assignee'].get('id')
            if instance.assignee_id != a_id:
                activity_list.append(Activity(
                    system=True,
                    template_id='task_assignee_changed',
                    task=instance,
                    sender=request.user,
                    target=User.objects.get(pk=a_id)
                ))
            instance.assignee_id = a_id

        if 'files' in request.data:
            files = map(lambda f: f.get('id'), request.data['files'])
            old_files = list(instance.files.values_list("id", flat=True))
            added = []
            for f in files:
                if f in old_files:
                    old_files.pop(old_files.index(f))
                else:
                    added.append(f)
                    activity_list.append(Activity(
                        system=True,
                        template_id='task_file_added',
                        task=instance,
                        sender=request.user,
                        target=FileManager.objects.get(pk=f)
                    ))

            for f in old_files:
                activity_list.append(Activity(
                    system=True,
                    template_id='task_file_deleted',
                    task=instance,
                    sender=request.user,
                    target=FileManager.objects.get(pk=f)
                ))

            instance.files.remove(*old_files)
            instance.files.add(*added)

        if instance.due_date != validated_data.get('due_date'):
            activity_list.append(Activity(
                system=True,
                template_id='task_date_changed',
                task=instance,
                sender=request.user
            ))

        if instance.priority != validated_data.get('priority'):
            activity_list.append(Activity(
                system=True,
                template_id='task_priority_changed',
                task=instance,
                sender=request.user
            ))

        if instance.status != validated_data.get('status'):
            activity_list.append(Activity(
                system=True,
                template_id='task_status_changed',
                task=instance,
                sender=request.user
            ))

        for key, value in validated_data.iteritems():
            setattr(instance, key, value)

        instance.save()

        for activity in activity_list:
            activity.save()

        return instance

    class Meta:
        model = Task
        fields = (
            'id', 'name', 'comment', 'due_date', 'assignee', 'files', 'priority', 'status',
            'get_priority_display', 'get_status_display', 'owner', 'activity_count', 'done', 'expired',
            'related_channel', 'related_channel_name'
        )


class ActivitySerializer(serializers.ModelSerializer):
    sender = FriendsSerializer(many=False, read_only=True)

    def create(self, validated_data):
        request = self.context['request']
        activity = Activity.objects.create(sender=request.user, **validated_data)
        return activity

    class Meta:
        model = Activity
        fields = ('id', 'sender', 'comment', 'created', 'task', 'system')
        readonly_fields = ('id', 'created', 'system')
