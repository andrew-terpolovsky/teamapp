(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('Models', ModelsManager);

    ModelsManager.$inject = [
        'AccountModel', 'SelfModel', 'UserLogout', 'Auth', 'Registration',
        'Invite', 'GetTZ', 'ResetPassword',
        'Friends', 'Tasks', 'Channel', 'Activity', 'Chat'
    ];

    /**
     *
     * @returns {ModelsManager}
     * @desc
     * @constructor
     */
    function ModelsManager(Acc, Self, UserLogout, Auth, Reg, Invite, GetTZ, ResetP, Friends, Tasks, Channel, Activity, Chat) {
        var self = this;
        self.AccountModel = Acc;
        self.SelfModel = Self;
        self.UserLogout = UserLogout;
        self.Auth = Auth;
        self.Registration = Reg;
        self.GetTZ = GetTZ;
        self.Invite = Invite;
        self.ResetPassword = ResetP;
        self.Friends = Friends;
        self.Tasks = Tasks;
        self.Activity = Activity;
        self.Channel = Channel;
        self.Chat = Chat;
        return self;
    }
})();
