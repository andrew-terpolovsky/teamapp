from django.contrib import admin
from doiq.tasks.models import Task, BaseTemplate


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    filter_horizontal = ['files', ]
    search_fields = ('name',)
    list_display = ('name', 'priority', 'assignee', 'status')
    list_filter = ('priority', 'status')


@admin.register(BaseTemplate)
class BaseTemplateAdmin(admin.ModelAdmin):
    search_fields = ('id',)
    list_display = ('id', '_get_html')
    list_filter = ('module',)

    def _get_html(self, obj):
        return obj.html

    _get_html.allow_tags = True
