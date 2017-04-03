from django.db.models.signals import Signal

channel_ownership_changed = Signal(providing_args=['channel', 'owner', 'new_owner'])
friend_added_to_channel = Signal(providing_args=['channel', 'friend', 'inviter'])
force_update_channel = Signal(providing_args=['channel', 'user'])
kicked_member_from_channel = Signal(providing_args=['membership', 'owner'])
file_binded_state_in_channel = Signal(providing_args=['channel_uid', 'file_id', 'deleted'])