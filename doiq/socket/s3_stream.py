import momoko
import uuid

from tornado import ioloop
from tornado import httpclient
from tornado.web import RequestHandler
from tornado import gen
from .authentication import SocketJWTAuthentication
from doiq.socket.raw_queries import QUERIES, ResultIter
from django.conf import settings
from django.utils import timezone
from django_s3_storage.storage import S3Storage
from zipfile import ZipFile, ZIP_DEFLATED
from StringIO import StringIO

s3_storage = S3Storage()

dsn = 'dbname=%s user=%s password=%s host=%s port=%s' % (
    settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'],
    settings.DATABASES['default']['HOST'], settings.DATABASES['default']['PORT'])
db = momoko.Pool(
    dsn=dsn,
    size=2,
    max_size=5,
    ioloop=ioloop.IOLoop.current(),
    # setsession=("SET TIME ZONE UTC",),
    raise_connect_errors=False,
    reconnect_interval=5 * 1000,
    auto_shrink=True,
    shrink_delay=timezone.timedelta(minutes=1)
)
db.connect()

class S3StreamBaseHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'X-Requested-With, Authorization')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    @gen.coroutine
    def authenticate_user(self, data):
        user = None
        try:
            backend = SocketJWTAuthentication()
            user, _ = backend.authenticate(data)
        except Exception as e:
            raise e
        return user

    @gen.coroutine
    def prepare(self, *args, **kwargs):
        setattr(self, 'user', None)

    @gen.coroutine
    def options(self, *args, **kwargs):
        pass

class S3StreamDownloadHandler(S3StreamBaseHandler):

    @gen.coroutine
    def get(self, jwt, msg_id):
        user = yield self.authenticate_user(jwt)
        if user:
            setattr(self, 'user', user)
        if self.user:
            cursor_check = yield db.execute(QUERIES.CHECK_USER_ACCESS_TO_MSG_FILES, (self.user.id, self.user.id, msg_id))
            if cursor_check.fetchone()[0] == 1:
                cursor_streamed_files = yield db.execute(QUERIES.GET_STREAMED_FILES_INFO, (msg_id, ))
                files = []
                s3_files = []
                for file_ in ResultIter(cursor_streamed_files, 500):
                    files.append(file_[1])
                    real_aws_url = s3_storage._generate_url(file_[0])
                    s3_files.append(httpclient.AsyncHTTPClient().fetch(real_aws_url))
                s3_raw_data = yield gen.multi(s3_files)
                print s3_raw_data, files
                in_memory_zip = StringIO()
                zip_file = ZipFile(in_memory_zip, 'w', ZIP_DEFLATED)
                for i, file_ in enumerate(files):
                    zip_file.writestr(file_, s3_raw_data[i].buffer.getvalue())
                zip_file.close()
                in_memory_zip.seek(0)
                zip_content = in_memory_zip.getvalue()
                self.set_header('Content-Type', 'application/zip')
                self.set_header('Content-Length', len(zip_content))
                self.set_header('Content-Disposition', 'attachment; filename=%s' % '{0}.zip'.format(str(uuid.uuid4())))
                self.flush()
                self.write(zip_content)
                self.finish()

class S3StreamSingleDownloadHandler(S3StreamBaseHandler):

    @gen.coroutine
    def get(self, jwt, msg_id='-', file_id=''):
        user = yield self.authenticate_user(jwt)
        if user:
            setattr(self, 'user', user)
        if self.user:
            if msg_id != '-':
                cursor_check = yield db.execute(QUERIES.CHECK_USER_ACCESS_TO_MSG_FILES, (self.user.id, self.user.id, msg_id))
                if cursor_check.fetchone()[0] == 1:
                    cursor_streamed_file = yield db.execute(QUERIES.GET_STREAMED_FILE_INFO, (msg_id, file_id))
                    file = cursor_streamed_file.fetchone()
                    real_aws_url = s3_storage._generate_url(file[0])
                    s3_raw_data = yield httpclient.AsyncHTTPClient().fetch(real_aws_url)
                    content = s3_raw_data.buffer.getvalue()
                    self.set_header('Content-Type', file[3])
                    self.set_header('Content-Length', len(content))
                    self.set_header('Content-Disposition', 'attachment; filename=%s' % '{0}'.format(file[1]))
                    self.flush()
                    self.write(content)
                    self.finish()
            else:
                cursor_streamed_file = yield db.execute(QUERIES.GET_STREAMED_FILE_INFO_NO_MESSAGE, (file_id, ))
                file = cursor_streamed_file.fetchone()
                real_aws_url = s3_storage._generate_url(file[0])
                s3_raw_data = yield httpclient.AsyncHTTPClient().fetch(real_aws_url)
                content = s3_raw_data.buffer.getvalue()
                self.set_header('Content-Type', file[3])
                self.set_header('Content-Length', len(content))
                self.set_header('Content-Disposition', 'attachment; filename=%s' % '{0}'.format(file[1]))
                self.flush()
                self.write(content)
                self.finish()