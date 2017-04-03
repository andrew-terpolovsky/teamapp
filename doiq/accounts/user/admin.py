from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin


class AccountAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'username', 'image', 'timezone')}),
        (_('Friends'), {'fields': ('friends',)}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('full_name', 'email')
    ordering = ('email',)
    list_display = ('email', 'full_name', 'timezone')
