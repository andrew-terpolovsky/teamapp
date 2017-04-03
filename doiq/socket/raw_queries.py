# coding: utf-8

def ResultIter(cursor, arraysize=1000):
    """
    An iterator that uses fetchmany to keep memory usage down
    """
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result


class Queries(object):
    def __setattr__(self, key, value):
        if hasattr(self, key):
            self.key = value
        else:
            super(Queries, self).__setattr__(key, value)

    def __getattr__(self, name):
        if hasattr(self, name):
            return super(Queries, self).__getattribute__(name)
        else:
            return None


QUERIES = Queries()

QUERIES.GET_USER_CHANNELS = 'SELECT c.channel_uid FROM channel_channelmembership cm ' \
                            'JOIN channel_channel c ON cm.channel_id = c.id ' \
                            'WHERE cm.member_id = %s;'

QUERIES.GET_CHANNEL_BY_UID = 'SELECT id, type, opened FROM channel_channel WHERE channel_uid = %s;'

QUERIES.INSERT_MESSAGE = 'INSERT INTO chat_chat(created, modified, message, channel_id, ' \
                         'recipient_id, sender_id, type) VALUES (%s, %s, %s, %s, %s, %s, 1) ' \
                         'RETURNING id;'

QUERIES.INSERT_MESSAGE_WITH_FILES = 'WITH ' \
                                    't1 AS (' \
                                    'INSERT INTO chat_chat' \
                                    '(created, modified, message, channel_id, recipient_id, sender_id, type) ' \
                                    'VALUES (%s, %s, %s, %s, %s, %s, 2) ' \
                                    'RETURNING id' \
                                    '), ' \
                                    't2 AS (SELECT t1.id, UNNEST(%s) as f_id FROM t1)' \
                                    'INSERT INTO chat_chat_files(chat_id, filemanager_id) ' \
                                    'SELECT t2.id, t2.f_id FROM t2 ' \
                                    'RETURNING chat_id'

QUERIES.INSERT_MESSAGE_NO_CHANNEL_ID = \
    """
    INSERT INTO chat_chat(created, modified, message, channel_id,
    recipient_id, sender_id, type) VALUES (%s, %s, %s,
    (SELECT id FROM channel_channel c WHERE c.channel_uid = %s),
    %s, %s, 1) RETURNING id;
    """

QUERIES.ADDED_FILES_INFO = 'SELECT * FROM filemanager_filemanager WHERE id = ANY(%s) AND owner_id = %s;'

QUERIES.GET_CHANNEL_MEMBERS_NO_SENDER = 'SELECT member_id FROM channel_channelmembership cm ' \
                                        'WHERE channel_id = %s AND member_id <> %s;'

QUERIES.UPDATE_UNREAD_COUNTER_TRANSACTION = [
    'SELECT cm.* FROM channel_channelmembership cm '
    'WHERE cm.channel_id = %s AND cm.member_id = ANY(%s) FOR UPDATE',

    'UPDATE channel_channelmembership cm '
    'SET counter_unread = counter_unread + 1 '
    'WHERE cm.channel_id = %s AND cm.member_id = ANY(%s)'
]

QUERIES.FLUSH_UNREAD_COUNTER_NO_CHANNEL_ID = 'WITH t AS(' \
                                             'SELECT id FROM channel_channel WHERE channel_uid = %s' \
                                             ')' \
                                             'UPDATE channel_channelmembership ' \
                                             'SET counter_unread = 0 ' \
                                             'WHERE member_id = %s AND channel_id = (SELECT id FROM t);'

QUERIES.CHECK_USER_ACCESS_TO_MSG_FILES = 'SELECT COUNT(chm.*) FROM chat_chat c ' \
                                         'JOIN channel_channel ch ON c.channel_id = ch.id ' \
                                         'JOIN channel_channelmembership chm ON ' \
                                         'chm.member_id = %s AND chm.channel_id = c.channel_id ' \
                                         'WHERE chm.member_id = %s AND c.id = %s;'

QUERIES.GET_STREAMED_FILES_INFO = 'SELECT f.file, f.original_name FROM chat_chat c ' \
                                  'JOIN chat_chat_files cf ON c.id = cf.chat_id ' \
                                  'JOIN filemanager_filemanager f ON f.id = cf.filemanager_id ' \
                                  'WHERE c.id = %s;'

QUERIES.GET_STREAMED_FILE_INFO = 'SELECT f.file, f.original_name, f.id, f.content_type FROM chat_chat c ' \
                                  'JOIN chat_chat_files cf ON c.id = cf.chat_id ' \
                                  'JOIN filemanager_filemanager f ON f.id = cf.filemanager_id ' \
                                  'WHERE c.id = %s AND f.id = %s;'

QUERIES.GET_STREAMED_FILE_INFO_NO_MESSAGE = 'SELECT f.file, f.original_name, f.id, f.content_type ' \
                                            'FROM filemanager_filemanager f ' \
                                            'WHERE f.id = %s;'

QUERIES.OPEN_INTERLOCUTOR_PRIVATE_CHANNEL = 'UPDATE channel_channelmembership ' \
                                            'SET private_channel_opened = true ' \
                                            'WHERE channel_id = %s AND member_id <> %s;'

QUERIES.REMOVE_DELETED_FILES_IN_CHANNEL = 'DELETE FROM chat_deletedfiles WHERE channel_id = %s AND file_id = ANY(%s);'
# QUERIES.MEMBERS_OF_ANY_CHANNEL = 'SELECT DISTINCT u.id, u.username FROM accounts_user u ' \
#                                  'JOIN channel_channelmembership cm ON u.id = cm.member_id '
