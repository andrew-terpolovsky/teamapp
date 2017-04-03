(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('AccountModel', AccountModel)
        .factory('SelfModel', SelfModel)
        .factory('UserLogout', UserLogout)
        .factory('Auth', Auth)
        .factory('Registration', Registration)
        .factory('GetTZ', GetTZ)
        .factory('Invite', Invite)
        .factory('ResetPassword', ResetPassword)
        .factory('FileManagerResource', FileManagerResource)
        .factory('Friends', Friends)
        .factory('Tasks', Tasks)
        .factory('Activity', Activity)
        .factory('Channel', Channel)
        .factory('Chat', Chat);


    AccountModel.$inject = ['Resource', 'Enums', 'Urls'];
    SelfModel.$inject = ['Resource', 'Enums', 'Urls'];
    UserLogout.$inject = ['Resource', 'Enums', 'Urls'];
    Auth.$inject = ['Resource', 'Enums', 'Urls'];
    Registration.$inject = ['Resource', 'Enums', 'Urls'];
    GetTZ.$inject = ['Resource', 'Enums', 'Urls'];
    Invite.$inject = ['Resource', 'Enums', 'Urls'];
    ResetPassword.$inject = ['Resource', 'Enums', 'Urls'];
    FileManagerResource.$inject = ['Resource', 'Enums', 'Urls'];
    Friends.$inject = ['Resource', 'Enums', 'Urls'];
    Tasks.$inject = ['Resource', 'Enums', 'Urls'];
    Activity.$inject = ['Resource', 'Enums', 'Urls'];
    Channel.$inject = ['Resource', 'Enums', 'Urls'];
    Chat.$inject = ['Resource', 'Enums', 'Urls'];

    /**
     *
     * @returns {AccountModel}
     * @constructor
     */
    function AccountModel($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.MODEL], {id: '@id'});
    }

    /**
     *
     * @returns {SelfModel}
     * @constructor
     */
    function SelfModel($resource, Enums, Urls) {
        return $resource(
            Urls[Enums.MODELS.ACCOUNT.SELF],
            {id: '@id'},
            {
                friend_delete: {
                    method: 'DELETE',
                    //url: Urls[Enums.FileManager.SCOPE.PERSONAL.ROOT],
                    isArray: false
                }
            }
        );
    }


    /**
     *
     * @returns {UserLogout}
     * @constructor
     */
    function UserLogout($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.LOGOUT]);
    }

    /**
     *
     * @returns {Auth}
     * @constructor
     */
    function Auth($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.AUTH]);
    }

    /**
     *
     * @returns {Registration}
     * @constructor
     */
    function Registration($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.REGISTRATION]);
    }

    /**
     *
     * @returns {GetTZ}
     * @constructor
     */
    function GetTZ($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.CORE.GET_TIMEZONES]);
    }

    /**
     *
     * @returns {InviteModel}
     * @constructor
     */
    function Invite($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.INVITE], {id: '@id'}, {
            'send': {method: 'POST', params: {verb: 'send'}},
            'resend': {method: 'PUT', params: {verb: 'resend'}}
        });
    }

    /**
     *
     * @returns {ResetPassword}
     * @constructor
     */
    function ResetPassword($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.RESET_PASSWORD]);
    }


    /**
     *
     * @returns {Friends}
     * @constructor
     */
    function Friends($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACCOUNT.FRIENDS]);
    }

    /**
     *
     * @returns {Tasks}
     * @constructor
     */
    function Tasks($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.TASKS.MODEL], {id: '@id'});
    }

    /**
     *
     * @returns {Activity}
     * @constructor
     */
    function Activity($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.ACTIVITY.MODEL], {id: '@id'});
    }

    /**
     *
     * @returns {Channel}
     * @constructor
     */
    function Channel($resource, Enums, Urls) {
        return $resource(
            Urls[Enums.MODELS.CHANNEL.MODEL],
            {id: '@id'},
            {
                archive: {
                    method: 'PUT',
                    isArray: false,
                    params: {id: '@channel_uid', action: 'archive'}
                },
                kick_member: {
                    method: 'DELETE',
                    url: Urls[Enums.MODELS.CHANNEL.KICK_MEMBER],
                    isArray: false,
                    params: {id: '@channel_uid', member_id: '@member_id'}
                },
                open_private_chat: {
                    method: 'PUT',
                    url: Urls[Enums.MODELS.CHANNEL.PRIVATE_CHANNEL],
                    isArray: false,
                    params: {friend_id: '@friend_id', action: 'open'}
                },
                close_private_chat: {
                    method: 'PUT',
                    url: Urls[Enums.MODELS.CHANNEL.PRIVATE_CHANNEL],
                    isArray: false,
                    params: {friend_id: '@friend_id', action: 'close'}
                },
                change_channel_owner: {
                    method: 'DELETE',
                    url: Urls[Enums.MODELS.CHANNEL.CHANGE_OWNER],
                    isArray: false,
                    params: {id: '@channel_uid', member_id: '@member_id'}
                }
            }
        );
    }

    /**
     *
     * @returns {Channel}
     * @constructor
     */
    function Chat($resource, Enums, Urls) {
        return $resource(Urls[Enums.MODELS.CHAT.MODEL], {id: '@id'}, {
            'query': { method: 'GET', isArray:false }
        });
    }


    /**
     *
     * @returns {FileManagerResource}
     * @constructor
     */
    function FileManagerResource($resource, Enums, Urls) {
        return $resource(
            Urls[Enums.FILEMANAGER.BASE_URL],
            {scope: 'personal'},
            {
                list: {
                    method: 'GET',
                    url: Urls[Enums.FILEMANAGER.SCOPE.PERSONAL.ROOT],
                    isArray: false,
                    params: {last_id: -1, limit: 10}
                },
                delete: {
                    method: 'POST',
                    url: Urls[Enums.FILEMANAGER.SCOPE.PERSONAL.ROOT],
                    isArray: false,
                    params: {scope: '@scope', action: 'delete'}
                }
            }
        );
    }
})();
