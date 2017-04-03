(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('Urls', UrlsManager);

    UrlsManager.$inject = [
        'Enums'
    ];

    /**
     *
     * @returns {UrlsManager}
     * @desc All application's urls here
     * @constructor
     */
    function UrlsManager(Enums) {
        var self = this;

        /* URLS */
        self.api = '/api/';
        // ACCOUNT
        self[Enums.MODELS.ACCOUNT.MODEL] = self.api + 'accounts/:id/';
        self[Enums.MODELS.ACCOUNT.SELF] = self.api + 'me/';
        self[Enums.MODELS.ACCOUNT.LOGOUT] = self.api + 'logout/';
        self[Enums.MODELS.ACCOUNT.FRIENDS] = self.api + 'friends/:id/';
        self[Enums.MODELS.ACCOUNT.AUTH] = self.api + 'token-auth/';
        self[Enums.MODELS.ACCOUNT.RESET_PASSWORD] = self.api + 'reset-password/';
        self[Enums.MODELS.ACCOUNT.REGISTRATION] = self.api + 'registration/';
        self[Enums.MODELS.ACCOUNT.INVITE] = self.api + 'invites/:id/:verb/';

        // TASKS
        self[Enums.MODELS.TASKS.MODEL] = self.api + 'tasks/:id/';
        self[Enums.MODELS.ACTIVITY.MODEL] = self.api + 'activity/:id/';

        //CHAT&CHANNEL
        self[Enums.MODELS.CHANNEL.MODEL] = self.api + 'channels/:id/';
        self[Enums.MODELS.CHANNEL.KICK_MEMBER] = self.api + 'channels/:id/kick_member/';
        self[Enums.MODELS.CHANNEL.CHANGE_OWNER] = self.api + 'channels/:id/change_owner/';
        self[Enums.MODELS.CHANNEL.PRIVATE_CHANNEL] = self.api + 'channels/private_channel/';
        self[Enums.MODELS.CHAT.MODEL] = self.api + 'chats/:id/';

        //FILE MANAGER
        self[Enums.FILEMANAGER.BASE_URL] = self.api + 'file-manager/';
        self[Enums.FILEMANAGER.SCOPE.PERSONAL.ROOT] = self[Enums.FILEMANAGER.BASE_URL] + ':scope/';
        self[Enums.FILEMANAGER.SCOPE.PERSONAL.UPLOAD_ROOT] = self[Enums.FILEMANAGER.BASE_URL] + 'personal/';

        //URLS
        self[Enums.MODELS.CORE.GET_TIMEZONES] = self.api + 'get-timezones/';
        self[Enums.MODELS.CORE.UPLOAD] = self.api + 'upload/';
        self[Enums.URLS.SOCKET_URL] = '/:9999/chat';

        //TEMPLATES
        self.templates = '/static/templates/';
        //TASKS
        self[Enums.TEMPLATES.TASKS.AUTOCOMPLETE] = self.templates + 'views/tasks/tasks-autocomplete.html';
        self[Enums.TEMPLATES.TASKS.MANAGE] = self.templates + 'views/tasks/manage-modal.html';
        self[Enums.TEMPLATES.TASKS.CHANNEL] = self.templates + 'views/tasks/channel-list-modal.html';

        //CHAT&CHANNEL
        self[Enums.TEMPLATES.CHANNEL.MANAGE] = self.templates + 'views/channels/modal.html';

        //ACCOUNT
        self[Enums.TEMPLATES.ACCOUNT.FRIENDS] = self.templates + 'views/accounts/friends.html';
        self[Enums.TEMPLATES.ACCOUNT.FILE_MANAGER] = self.templates + 'views/filemanager/modal.html';

        //CORE
        self[Enums.TEMPLATES.CORE.DELETE] = self.templates + 'views/core/delete-modal.html';

        return self;
    }

})();
