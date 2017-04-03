from django.core.signals import Signal

user_profile_was_changed = Signal(providing_args=['user', 'picture_small', 'full_name'])