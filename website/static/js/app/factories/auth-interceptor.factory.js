(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('authInterceptor', authInterceptor);

    authInterceptor.$inject = ['$q', '$rootScope', 'AuthService', 'Socket'];

    function authInterceptor($q, $rootScope, AuthService, Socket) {
        var self = this;

        self.request = function (config) {
            config.headers = config.headers || {};
            if (AuthService.isAuthorized()) {
                config.headers['Authorization'] = 'JWT ' + AuthService.getToken();
            }
            return config;
        };

        self.responseError = function (rejection) {
            if (rejection.status === 401) {
                AuthService.deleteToken();
                $rootScope.$broadcast('unauthorized');
                $rootScope.user ? (function () {
                    delete $rootScope.user
                })() : null;
                Socket.close();
            }
            return $q.reject(rejection);
        };

        return self;
    }
})();
