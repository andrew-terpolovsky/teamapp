from django.contrib import admin
from doiq.accounts.models import User, Invite
from .invites.admin import InviteAdmin
from .user.admin import AccountAdmin

admin.site.register(User, AccountAdmin)
admin.site.register(Invite, InviteAdmin)