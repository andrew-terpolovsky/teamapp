# coding: utf-8
import itertools
import json
import logging

import tornadoredis
from django.utils import timezone
from django.utils.html import escape
from django_s3_storage.storage import S3Storage
from doiq.socket.raw_queries import QUERIES, ResultIter
from sorl.thumbnail import get_thumbnail
from tornado import gen
from tornado import ioloop
from .base_handler import BaseSocketHandler

s3_storage = S3Storage()


class ChatSocketHandler(BaseSocketHandler):
    @gen.coroutine
    def flatten_receivers(self, channel):
        user_receivers_connections = ChatSocketHandler._bindings['channel_connected_users'].get(channel, set())
        print user_receivers_connections, ChatSocketHandler._bindings['channel_connected_users']
        user_receivers_connections = dict(
            (key, ChatSocketHandler._bindings['connections_by_user_id'].get(key, set())) for key in
            user_receivers_connections)
        flattened_receivers_connections = itertools.chain(*user_receivers_connections.values())
        raise gen.Return(flattened_receivers_connections)

    @staticmethod
    @gen.coroutine
    def cls_flatten_receivers(channel):
        user_receivers_connections = ChatSocketHandler._bindings['channel_connected_users'].get(channel, set())
        print user_receivers_connections, ChatSocketHandler._bindings['channel_connected_users']
        user_receivers_connections = dict(
            (key, ChatSocketHandler._bindings['connections_by_user_id'].get(key, set())) for key in
            user_receivers_connections)
        flattened_receivers_connections = itertools.chain(*user_receivers_connections.values())
        raise gen.Return(flattened_receivers_connections)

    @staticmethod
    @gen.coroutine
    def update_user_channels(user_id):
        logging.debug(['Updating user channels: ', user_id])
        user_available_channels_cursor = yield ChatSocketHandler.db.execute(QUERIES.GET_USER_CHANNELS, (user_id,))
        for chnls in ResultIter(user_available_channels_cursor, 500):
            print chnls
            user_available_channels = ChatSocketHandler._bindings['user_available_channels'].get(user_id, None)
            if not user_available_channels:
                user_available_channels = set()
            user_available_channels = user_available_channels.union(chnls)
            ChatSocketHandler._bindings['user_available_channels'][user_id] = user_available_channels

            for chnl in chnls:
                channel_connected_users = ChatSocketHandler._bindings['channel_connected_users'].get(chnl, None)
                if not channel_connected_users:
                    channel_connected_users = set()
                channel_connected_users.add(user_id)
                ChatSocketHandler._bindings['channel_connected_users'][chnl] = channel_connected_users

    @gen.coroutine
    def king(self):
        return 'kong'

    @gen.coroutine
    def register_in_channel(self, channel):
        logging.debug(['Register in channel', self.user])
        # ToDo has permissions to channel
        registered_channels = getattr(self, 'registered_channels', set())
        registered_channels.add(channel)
        setattr(self, 'registered_channels', registered_channels)
        # yield self.db.execute(QUERIES.FLUSH_UNREAD_COUNTER_NO_CHANNEL_ID, (channel, self.user.id))
        ioloop.IOLoop.current().spawn_callback(
            self.db.execute,
            QUERIES.FLUSH_UNREAD_COUNTER_NO_CHANNEL_ID,
            (channel, self.user.id)
        )

    @gen.coroutine
    def unregister_from_channel(self, channel):
        logging.debug(['De-register from channel', self.user])
        # ToDo has permissions to channel
        registered_channels = getattr(self, 'registered_channels', set())
        if channel in registered_channels:
            registered_channels.remove(channel)
            setattr(self, 'registered_channels', registered_channels)

    @gen.coroutine
    def authorize(self, tokenJWT):
        logging.debug(['authorize', self.session.conn_info.ip])
        if (not hasattr(self, 'user') or self.user is None) and tokenJWT:
            try:
                self.user = self.authenticate_user(tokenJWT)
                cropped_avatar = None
                if self.user.image:
                    cropped_avatar = ChatSocketHandler._bindings['avatars'].get(self.user.id)
                    if not cropped_avatar:
                        cropped_avatar = get_thumbnail(self.user.image.file, '52x52', crop='center', quality=100,
                                                       format='PNG').url
                        ChatSocketHandler._bindings['avatars'][self.user.id] = cropped_avatar
                setattr(self.user, 'cropped_avatar', cropped_avatar)
            except Exception as e:
                setattr(self.user, 'cropped_avatar', '/static/img/profile.png')
                logging.error(e)

        if self.user is not None:
            ChatSocketHandler._bindings['users_by_id'][self.user.id] = self.user
            user_connections = ChatSocketHandler._bindings['connections_by_user_id'].get(self.user.id, None)
            if not user_connections:
                user_connections = set()
            if self not in user_connections:
                user_connections.add(self)
            ChatSocketHandler._bindings['connections_by_user_id'][self.user.id] = user_connections
            yield ChatSocketHandler.update_user_channels(self.user.id)
            ioloop.IOLoop.current().spawn_callback(self.propagate_user_statuses, **{'online': self.user.id})

    @gen.coroutine
    def open_interlocutor_private_chat(self, channel):
        channel_cursor = yield self.db.execute(QUERIES.GET_CHANNEL_BY_UID, (channel,))
        channel_id, type, opened = channel_cursor.fetchone()
        if type == 1:
            yield self.db.execute(QUERIES.OPEN_INTERLOCUTOR_PRIVATE_CHANNEL, (channel_id, self.user.id))
        raise gen.Return(type)

    @gen.coroutine
    def check_channel_is_opened(self, channel):
        channel_cursor = yield self.db.execute(QUERIES.GET_CHANNEL_BY_UID, (channel,))
        channel_id, type, opened = channel_cursor.fetchone()
        raise gen.Return(opened)

    @gen.coroutine
    def message(self, channel, input):
        print '\n', self.user.cropped_avatar, '\n'
        channel_type = yield self.open_interlocutor_private_chat(channel)
        if channel_type != 1:
            is_opened = yield self.check_channel_is_opened(channel)
            if not is_opened:
                message_struct = {'error': True, 'reason': 'not_opened'}
                message_struct = self.render_message(message_struct)
                raise gen.Return(message_struct)
        logging.debug(['message'])
        if (not hasattr(self, 'user') or self.user is None):
            raise ValueError('No access.')

        if self.user is not None and input:
            input = (escape(input.encode('utf-8')))
            logging.error(input)
            flattened_receivers_connections = yield self.flatten_receivers(channel)
            timestamp = timezone.now()
            if timezone.is_naive(timestamp):
                timestamp = timezone.make_aware(timestamp, timezone.utc)
            timestamp = timestamp
            message_id_cursor = yield self.db.execute(
                QUERIES.INSERT_MESSAGE_NO_CHANNEL_ID,
                (timestamp, timestamp, input, channel, None, self.user.id)
            )
            message_id = message_id_cursor.fetchone()[0]
            message_struct = {
                'id': message_id,
                'channel_uid': channel,
                'channel_type': channel_type,
                'created': timestamp,
                'message': input,
                'type': 1,
                'user_id': self.user.id,
                'user_name': self.user.full_name or self.user.username or self.user.email,
                'sender': {
                    'full_name': self.user.full_name,
                    'username': self.user.username,
                    'email': self.user.email,
                    'id': self.user.id,
                    'image': self.user.cropped_avatar
                }
            }
            message_struct = self.render_message(message_struct)
            # Todo remove
            flattened_receivers_connections = list(flattened_receivers_connections)
            logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
            for x in flattened_receivers_connections:
                if x == self:
                    continue
                x.emit('receive_message', message_struct)  # , self.ack_update_counter)
            ioloop.IOLoop.current().spawn_callback(self.update_unread_counter, *(channel, self.user.id))
            raise gen.Return(message_struct)
        raise gen.Return(None)

    @gen.coroutine
    def update_unread_counter(self, channel, sender):
        channel_id_cursor = yield self.db.execute(QUERIES.GET_CHANNEL_BY_UID, (channel,))
        channel_id = channel_id_cursor.fetchone()[0]
        members_cursor = yield self.db.execute(QUERIES.GET_CHANNEL_MEMBERS_NO_SENDER, (channel_id, sender))
        members_not_delivered = []
        for x in ResultIter(members_cursor, 500):
            member_id = x[0]
            connections_by_user_id = ChatSocketHandler._bindings['connections_by_user_id'].get(member_id, [])
            if not connections_by_user_id:
                members_not_delivered.append(member_id)
            else:
                not_delivered = True
                for ch in itertools.chain(*(getattr(y, 'registered_channels', []) for y in connections_by_user_id)):
                    if ch == channel:
                        not_delivered = False
                        break
                if not_delivered:
                    members_not_delivered.append(member_id)
        if members_not_delivered:
            yield self.db.transaction(
                [
                    (QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION[0], (channel_id, members_not_delivered)),
                    (QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION[1], (channel_id, members_not_delivered))
                ]
            )

    @gen.coroutine
    def trigger_update_channels(self):
        yield self.update_user_channels(self.user.id)

    # @gen.coroutine
    # def ack_update_counter(self, future):
    #     ack_future_result = future.result()
    #
    #     if ack_future_result['unread']:
    #         # q=yield self.db.mogrify(
    #         #     QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION[1],(
    #         #         ack_future_result['channel'],
    #         #         ack_future_result['unread'],
    #         #         self.user.id,
    #         #     )
    #         # )
    #         # print q
    #         cursors = yield self.db.transaction([
    #             (QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION[0], (ack_future_result['channel'], )),
    #             (QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION[1], (
    #                 ack_future_result['channel'],
    #                 ack_future_result['unread'],
    #                 self.user.id,
    #             ))]
    #         )

    @gen.coroutine
    def add_files_to_channel(self, channel, files):
        channel_type = yield self.open_interlocutor_private_chat(channel)
        if channel_type != 1:
            is_opened = yield self.check_channel_is_opened(channel)
            if not is_opened:
                message_struct = {'error': True, 'reason': 'not_opened'}
                message_struct = self.render_message(message_struct)
                raise gen.Return(message_struct)
        if self.user is not None and files:
            channel_type = yield self.open_interlocutor_private_chat(channel)
            files_info_cursor = yield self.db.execute(QUERIES.ADDED_FILES_INFO, (files, self.user.id))
            channel_id_cursor = yield self.db.execute(QUERIES.GET_CHANNEL_BY_UID, (channel,))
            channel_id = channel_id_cursor.fetchone()[0]
            returning_info = []
            files_data_to_insert = []
            timestamp = timezone.now()
            if timezone.is_naive(timestamp):
                timestamp = timezone.make_aware(timestamp, timezone.utc)
            files_ids = []
            for file_ in ResultIter(files_info_cursor, 500):
                print file_
                aws_file_url = s3_storage._generate_url(file_[1])
                aws_file_preview_url = s3_storage._generate_url(file_[6])
                returning_info.append({
                    'file': aws_file_url,
                    'file_preview': aws_file_preview_url,
                    'id': file_[0],
                    'original_name': file_[3],
                    'content_type': file_[2],
                    'size': file_[4],
                    'owner': self.user.id
                })
                files_ids.append(file_[0])

                # timestamp = timestamp.strftime('\'%Y-%m-%d %H:%M:%S\'')
                files_data_to_insert.append(
                    (timestamp, timestamp, 'null', str(channel_id), 'null', str(self.user.id), str(file_[0])))
            yield self.db.execute(QUERIES.REMOVE_DELETED_FILES_IN_CHANNEL, (channel_id, files_ids))

            message_id_cursor = yield self.db.execute(
                QUERIES.INSERT_MESSAGE_WITH_FILES,
                (timestamp, timestamp, None, channel_id, None, self.user.id, files)
            )
            message_id = message_id_cursor.fetchone()[0]

            returning_info = {
                'owner': self.user.id,
                'id': message_id,
                'files': returning_info,
                'channel_type': channel_type,
                'type': 2,
                'channel_uid': channel,
                'channel': channel_id,
                'created': timestamp,
                'user_id': self.user.id,
                'avatar': self.user.cropped_avatar,
                'user_name': self.user.full_name or self.user.username or self.user.email,
                'sender': {
                    'full_name': self.user.full_name,
                    'username': self.user.username,
                    'email': self.user.email,
                    'id': self.user.id,
                    'image': self.user.cropped_avatar
                }
            }
            binded_files_struct = self.render_message(returning_info)
            flattened_receivers_connections = yield self.flatten_receivers(channel)
            flattened_receivers_connections = list(flattened_receivers_connections)
            logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
            for x in flattened_receivers_connections:
                if x == self:
                    continue
                x.emit('receive_files', binded_files_struct)
            ioloop.IOLoop.current().spawn_callback(self.update_unread_counter, *(channel, self.user.id))
            raise gen.Return(binded_files_struct)
        raise gen.Return(None)

    @gen.coroutine
    def someone_is_typing(self, channel, typing):
        channel_typing = ChatSocketHandler._bindings['typing'].get(channel, {})
        if not typing:
            if self.user.id in channel_typing.keys():
                channel_typing.pop(self.user.id)
        else:
            channel_typing[self.user.id] = {
                'username': self.user.username,
                'full_name': self.user.full_name
            }
        ChatSocketHandler._bindings['typing'][channel] = channel_typing
        flattened_receivers_connections = yield self.flatten_receivers(channel)
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        typings = self.render_message(channel_typing)
        for x in flattened_receivers_connections:
            if x == self:
                continue
            x.emit('someone_is_typing', typings)

    @staticmethod
    @gen.coroutine
    def notification_channel_kicked_member(channel, notification):
        flattened_receivers_connections = yield ChatSocketHandler.cls_flatten_receivers(channel)
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification['channel_uid'] = channel
        notification = {'data': notification, 'type': 'kicked_member'}
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            # if x == self:
            #     continue
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_add_invitee_as_friend_to_inviter(user_id, friend, member_of_channel):
        flattened_receivers_connections = ChatSocketHandler._bindings['connections_by_user_id'].get(user_id, set())
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers n friendship to inviter: ', len(flattened_receivers_connections)])
        friend['channel_uid'] = member_of_channel
        notification = {'data': friend, 'type': 'friend_accept_invite'}
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_channel_archived(channel):
        flattened_receivers_connections = yield ChatSocketHandler.cls_flatten_receivers(channel['channel_uid'])
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification = {'data': channel, 'type': 'channel_archived'}
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            # if x == self:
            #     continue
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_channel_ownership_changed(channel, user_id):
        flattened_receivers_connections = ChatSocketHandler._bindings['connections_by_user_id'].get(user_id, set())
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification = {'data': channel, 'type': 'channel_ownership_changed'}
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            # if x == self:
            #     continue
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_friend_added_to_channel(channel, user_id):
        flattened_receivers_connections = ChatSocketHandler._bindings['connections_by_user_id'].get(user_id, set())
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(
            ['notification_friend_added_to_channel', 'Found receivers: ', len(flattened_receivers_connections)])
        notification = {'data': channel, 'type': 'friend_added_to_channel'}
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            # if x == self:
            #     continue
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_member_added_to_channel(channel_uid, user, message=None):
        flattened_receivers_connections = yield ChatSocketHandler.cls_flatten_receivers(channel_uid)
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification = {'data': {'channel_uid': channel_uid, 'user': user, 'message': message}, 'type': 'member_added_to_channel'}

        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            # if x == self:
            #     continue
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_profile_changed(**kwargs):
        user_id = kwargs.get('user_id')
        avatar = kwargs.get('avatar')
        full_name = kwargs.get('full_name')
        print '           ,', avatar, user_id
        ChatSocketHandler._bindings['avatars'][user_id] = avatar
        flattened_receivers_connections = ChatSocketHandler._bindings['connections_by_user_id'].get(user_id, set())
        for x in flattened_receivers_connections:
            if avatar:
                setattr(x.user, 'cropped_avatar', avatar)
            if full_name:
                setattr(x.user, 'full_name', full_name)
            print x, 'change avatar'
        yield ChatSocketHandler.update_user_channels(user_id)
        all_channels_where_changes_are_needed = ChatSocketHandler._bindings['user_available_channels'][user_id]
        notification = {'data': {'user_id': user_id}, 'type': 'profile_changed'}
        if avatar:
            notification['data']['avatar'] = avatar
        if full_name:
            notification['data']['full_name'] = full_name
        notification = ChatSocketHandler.cls_render_message(notification)
        bulk_data = {}
        for chnl in all_channels_where_changes_are_needed:
            users = ChatSocketHandler._bindings['channel_connected_users'].get(chnl, [])
            print 'USERS: '
            for usr in users:
                if user_id == usr: continue
                if usr not in bulk_data.keys():
                    bulk_data[usr] = set()
                to_update_clients = ChatSocketHandler._bindings['connections_by_user_id'].get(usr, set())
                for client in to_update_clients:
                    bulk_data[usr].add(client)
        for clients_set in bulk_data.values():
            for client in clients_set:
                client.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_channel_tasks_modified(channel_uid, notification):
        flattened_receivers_connections = yield ChatSocketHandler.cls_flatten_receivers(channel_uid)
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification = {
            'data': {
                'channel_uid': channel_uid,
                'notification': notification
            },
            'type': 'channel_tasks_modified'
        }
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            x.emit('receive_notification', notification)

    @staticmethod
    @gen.coroutine
    def notification_file_binded_state_in_channel(channel_uid, deleted, file_id):
        flattened_receivers_connections = yield ChatSocketHandler.cls_flatten_receivers(channel_uid)
        flattened_receivers_connections = list(flattened_receivers_connections)
        logging.debug(['Found receivers: ', len(flattened_receivers_connections)])
        notification = {
            'data': {
                'channel_uid': channel_uid,
                'deleted': deleted,
                'file_id': file_id
            },
            'type': 'file_binded_state_in_channel'
        }
        notification = ChatSocketHandler.cls_render_message(notification)
        for x in flattened_receivers_connections:
            print x.user
            x.emit('receive_notification', notification)


class AsyncRedisListener(object):
    def __init__(self, *args, **kwargs):
        self.client = tornadoredis.Client(
            selected_db=8,
            host='localhost',
            port=6379
        )
        self.client.connect()
        self.listen(['channels_todo', 'friendship_todo', 'user_todo'])

    @gen.coroutine
    def listen(self, channels):
        yield gen.Task(self.client.subscribe, channels)
        self.client.listen(self.handle_message)

    @gen.coroutine
    def handle_message(self, msg):
        try:
            msg = json.loads(msg.body)

            if msg['type'] == 'update_channel_connected_users':
                yield ChatSocketHandler.update_user_channels(msg['user']['id'])
                if msg.get('channel_uid'):
                    yield ChatSocketHandler.notification_member_added_to_channel(msg['channel_uid'], msg['user'], msg['message'])
            if msg['type'] == 'add_invitee_as_friend_to_inviter':
                yield ChatSocketHandler.notification_add_invitee_as_friend_to_inviter(
                    msg['user_id'], msg['friend'], msg['member'])
            if msg['type'] == 'channel_archived':
                yield ChatSocketHandler.notification_channel_archived(msg['channel'])
            if msg['type'] == 'channel_kicked_member':
                yield ChatSocketHandler.notification_channel_kicked_member(msg['channel_uid'], msg['notification'])
            if msg['type'] == 'channel_ownership_changed':
                yield ChatSocketHandler.notification_channel_ownership_changed(msg['channel'], msg['user_id'])
            if msg['type'] == 'friend_added_to_channel':
                yield ChatSocketHandler.notification_friend_added_to_channel(msg['channel'], msg['user_id'])
            if msg['type'] == 'profile_changed':
                msg.pop('type')
                print msg
                yield ChatSocketHandler.notification_profile_changed(**msg)
            if msg['type'] == 'channel_tasks_modified':
                yield ChatSocketHandler.notification_channel_tasks_modified(msg['channel_uid'], msg['notification'])
            if msg['type'] == 'file_binded_state_in_channel':
                yield ChatSocketHandler.notification_file_binded_state_in_channel(msg['channel'], msg['deleted'], msg['file_id'])

        except Exception as e:
            print 'Error in parsing channel msg', type(e), str(e)


listener = AsyncRedisListener()