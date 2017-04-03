from celery.task import task
from django.utils import timezone

from doiq.tasks.models import Task


@task(queue='low-priority-queue')
def foo():
    Task.objects.filter(status=3, modified__lt=timezone.now() - timezone.timedelta(days=7)).update(deleted=True)
