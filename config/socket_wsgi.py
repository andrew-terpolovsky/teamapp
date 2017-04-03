"""
WSGI config for doiqapp tornado socket server.
"""

import os
import sys

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'settings.local')

from boto.file.key import Key
from tornado import web
from tornado.httpserver import HTTPServer
from tornado import ioloop
from sockjs.tornado import SockJSRouter
import django
from django.conf import settings
from django.utils.module_loading import import_module

def get_class():
    sockjs = settings.SOCKJS_CLASSES
    module_name, cls_name = sockjs[0].rsplit('.', 1)
    module = import_module(module_name)

    return getattr(module, cls_name)


def get_channel():
    _channel = settings.SOCKJS_CHANNEL
    return _channel.startswith('/') and _channel or '/%s' % _channel


def get_router(cls, channel):
    return SockJSRouter(cls, channel)


def get_app_setings():
    return dict(debug=settings.DEBUG, websocket_allow_origin='*')

def get_s3_stream_download_handler():
    module = import_module('doiq.socket.s3_stream')
    return getattr(module, 'S3StreamDownloadHandler')

def get_s3_single_stream_download_handler():
    module = import_module('doiq.socket.s3_stream')
    return getattr(module, 'S3StreamSingleDownloadHandler')

def get_tornado_application():
    django.setup()
    return web.Application(
        [
            (r'/bulk-download-message-files/(?P<jwt>.+)/(?P<msg_id>\d+)/', get_s3_stream_download_handler()),
            (r'/download-message-file/(?P<jwt>.+)/(?P<msg_id>\d+|-)/(?P<file_id>\d+)/', get_s3_single_stream_download_handler())
         ] + get_router(get_class(), get_channel()).urls, **get_app_setings())


if __name__ == "__main__":
    import logging

    logging.getLogger().setLevel(logging.DEBUG)
    application = get_tornado_application()
    HTTPServer(application, no_keep_alive=True).listen(9999)

    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        pass
