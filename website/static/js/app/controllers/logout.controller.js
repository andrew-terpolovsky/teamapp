(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .controller('LogoutController', LogoutController);

    LogoutController.$inject = ['$rootScope', 'AuthService', 'Socket'];

    function LogoutController($rootScope, AuthService, Socket) {
        if (AuthService.isAuthorized()) {
            AuthService.deleteToken();
            $rootScope.user ? (function () {
                delete $rootScope.user
            })() : null;
            Socket.close();
        }
    }
})();