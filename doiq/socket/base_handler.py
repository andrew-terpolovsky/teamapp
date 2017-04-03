import uuid
import json
import os
import logging
from functools import partial

import momoko
import tornadoredis
from tornado import gen
from tornado import ioloop
import django
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.six import BytesIO
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from django.conf import settings
from sockjs.tornado import SockJSConnection

from .authentication import SocketJWTAuthentication


logger = logging.getLogger('socket')

dsn = 'dbname=%s user=%s password=%s host=%s port=%s' % (
    settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'],
    settings.DATABASES['default']['HOST'], settings.DATABASES['default']['PORT'])
db = momoko.Pool(
    dsn=dsn,
    size=2,
    max_size=20,
    ioloop=ioloop.IOLoop.current(),
    # setsession=("SET TIME ZONE UTC",),
    raise_connect_errors=False,
    reconnect_interval=5 * 1000,
    auto_shrink=True,
    shrink_delay=timezone.timedelta(minutes=1)
)
db.connect()


class BaseSocketHandler(SockJSConnection):
    """
    Base client-server logic implementation.
    """
    _bindings = {}
    _bindings['connections_by_user_id'] = {}
    _bindings['users_by_id'] = {}
    _bindings['user_available_channels'] = {}
    _bindings['channel_connected_users'] = {}
    _bindings['online_users'] = set()
    _bindings['typing'] = {}
    _bindings['avatars'] = {}
    _participants = set()
    _pending_futures = {}

    REDIS_CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=10,
                                                        wait_for_available=True)

    db = db

    def __init__(self, *args, **kwargs):
        self.logger = logger
        super(BaseSocketHandler, self).__init__(*args, **kwargs)
        self.db = db

    def on_open(self, request):
        self.user = None
        self._participants.add(self)

    @gen.coroutine
    def on_message(self, msg):
        """Message receiver"""
        msg = self.parse_message(msg)
        logging.debug(msg)
        event = msg.get('event', None)
        kwargs = msg.get('kwargs', {})
        acknowledge = msg.get('acknowledge', None)
        print BaseSocketHandler._pending_futures.keys(), acknowledge in BaseSocketHandler._pending_futures.keys()
        if event != 'ack_callback':
            if not hasattr(self, event):
                raise Exception
            future = getattr(self, event)(**kwargs)
            print acknowledge, event
            complete_callback = partial(self.on_event_complete, *(acknowledge, event))
            ioloop.IOLoop.current().add_future(future, complete_callback)
        elif event == 'ack_callback' and acknowledge and acknowledge in BaseSocketHandler._pending_futures.keys():
            future = BaseSocketHandler._pending_futures.pop(acknowledge)
            future.set_result(kwargs)
            future.done()


    def on_close(self):
        """Close socket connection to client"""
        self._participants.remove(self)
        if self.user:
            connections_by_user_id = BaseSocketHandler._bindings['connections_by_user_id'].get(self.user.id, [])
            if self in connections_by_user_id:
                logger.debug(['Closing connection', self.user])
                connections_by_user_id.remove(self)
                if connections_by_user_id:
                    BaseSocketHandler._bindings['connections_by_user_id'][self.user.id] = connections_by_user_id
                else:
                    ioloop.IOLoop.current().spawn_callback(self.propagate_user_statuses,
                                                                 **{'offline': self.user.id})

    @gen.coroutine
    def on_event_complete(self, acknowledge, event, future):
        result = future.result()
        self.send(
            {
                'acknowledge': acknowledge,
                'event': event,
                'type': 'message',
                'result': result
            }
        )

    def remove_pending_future(self, acknowledge):
        if acknowledge in BaseSocketHandler._pending_futures.keys():
            BaseSocketHandler._pending_futures.pop(acknowledge)

    @gen.coroutine
    def emit(self, event, data, ack_callback=None):
        acknowledge = str(uuid.uuid4())
        self.send(
            {
                'acknowledge': acknowledge,
                'type': 'event',
                'event': event,
                'data': data
            }
        )
        if ack_callback:
            future = gen.Future()
            BaseSocketHandler._pending_futures[acknowledge] = future
            ioloop.IOLoop.current().add_future(future, ack_callback)
            ioloop.IOLoop.current().add_timeout(timezone.timedelta(minutes=1), self.remove_pending_future, *(acknowledge, ))


    @gen.coroutine
    def propagate_user_statuses(self, online=None, offline=None):
        if online:
            BaseSocketHandler._bindings['online_users'].add(online)
        if offline:
            try:
                BaseSocketHandler._bindings['online_users'].remove(offline)
            except:
                pass
        logging.error(BaseSocketHandler._participants)
        for x in BaseSocketHandler._participants:
            x.emit('online_statuses', json.dumps(list(BaseSocketHandler._bindings['online_users'])))
        # members_all_cursor = yield self.db.execute(QUERIES.MEMBERS_OF_ANY_CHANNEL)
        # print members_all_cursor.fetchall()

    def authenticate_user(self, data):
        user = None
        try:
            backend = SocketJWTAuthentication()
            user, _ = backend.authenticate(data)
        except Exception as e:
            raise e
        return user

    def render_message(self, msg):
        return JSONRenderer().render(msg)

    @staticmethod
    def cls_render_message(msg):
        return JSONRenderer().render(msg)

    def parse_message(self, msg):
        return JSONParser().parse(BytesIO(msg.encode('utf-8')))
