from django.contrib import admin


class InviteAdmin(admin.ModelAdmin):
    list_display = ('email', 'invited_by', 'accepted')
