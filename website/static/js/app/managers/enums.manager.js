(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('Enums', Enums);

    Enums.$inject = [];

    function Enums() {
        return {
            TOKEN: 'DoIq.token',
            MODELS: {
                ACCOUNT: {
                    SELF: 'USER_MODEL_SELF',
                    MODEL: 'USER_MODEL',
                    LOGOUT: 'USER_LOGOUT',
                    RESET_PASSWORD: 'RESET_PASSWORD',
                    FRIENDS: 'FRIENDS',
                    AUTH: 'AUTH_TOKEN',
                    REGISTRATION: 'REGISTRATION',
                    INVITE: 'INVITE'
                },
                CORE: {
                    GET_TIMEZONES: "GET_TIMEZONES",
                    UPLOAD: "UPLOAD"
                },
                TASKS: {
                    MODEL: 'TASKS_MODEL'
                },
                ACTIVITY: {
                    MODEL: 'ACTIVITY_MODEL'
                },
                CHANNEL: {
                    MODEL: 'CHANNEL_MODEL',
                    KICK_MEMBER: 'CHANNEL_KICK_MEMBER',
                    PRIVATE_CHANNEL: 'CHANNEL_GET_PRIVATE_CHANNEL'
                },
                CHAT: {
                    MODEL: 'CHAT_MODEL'
                }
            },
            FILEMANAGER: {
                BASE_URL: 'FM_BASE_URL',
                SCOPE: {
                    PERSONAL: {
                        ROOT: 'FM_SCOPE_PERSONAL_ROOT',
                        UPLOAD_ROOT: 'FM_SCOPE_PERSONAL_UPLOAD_ROOT'
                    }
                }
            },
            URLS: {
                SOCKET_URL: "SOCKET_URL"
            },
            TEMPLATES: {
                TASKS: {
                    MANAGE: 'TASKS_MANAGE',
                    AUTOCOMPLETE: 'AUTOCOMPLETE',
                    LIST: 'TASKS_LIST',
                    CHANNEL: 'TASKS_CHANNEL_LIST'
                },
                CHANNEL: {
                    MANAGE: 'CHANNEL_MANAGE'
                },
                ACCOUNT: {
                    FRIENDS: 'ACCOUNT_FRIENDS_MANAGE',
                    FILE_MANAGER: 'ACCOUNT_FILE_MANAGER'
                },
                CORE: {
                    DELETE: 'CORE_DELETE_MODAL'
                }
            }
        };
    }
})();
