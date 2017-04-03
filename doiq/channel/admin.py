from django.contrib import admin
from doiq.channel.models import Channel, ChannelMembership
# Register your models here.

admin.site.register(Channel)
admin.site.register(ChannelMembership)