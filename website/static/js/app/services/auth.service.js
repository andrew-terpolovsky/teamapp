(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .service('AuthService', AuthService);

    AuthService.$inject = ['$window', 'Enums'];

    function AuthService($window, Enums) {
        var self = this;

        self.urlBase64Decode = function (str) {
            var output = str.replace(/-/g, '+').replace(/_/g, '/');
            switch (output.length % 4) {
                case 0:
                    break;
                case 2:
                    output += '==';
                    break;
                case 3:
                    output += '=';
                    break;
                default:
                    throw 'Illegal base64url string!';
            }
            return $window.decodeURIComponent($window.atob(output));
        };

        self.getToken = function () {
            return localStorage.getItem(Enums.TOKEN);
        };

        self.setToken = function (key) {
            return localStorage.setItem(Enums.TOKEN, key);
        };

        self.deleteToken = function () {
            localStorage.removeItem(Enums.TOKEN);
        };

        self.decodeToken = function (token) {
            token = self.getToken(token);

            var parts = token.split('.');

            if (parts.length !== 3) {
                throw new Error('JWT must have 3 parts');
            }

            var decoded = self.urlBase64Decode(parts[1]);
            if (!decoded) {
                throw new Error('Cannot decode the token');
            }

            return angular.fromJson(decoded);
        };


        self.getTokenExpirationDate = function () {
            var decoded = self.decodeToken(Enums.TOKEN);

            if (typeof decoded.exp === "undefined") {
                return null;
            }

            var d = new Date(0); // The 0 here is the key, which sets the date to the epoch
            d.setUTCSeconds(decoded.exp);

            return d;
        };

        self.isTokenExpired = function (offsetSeconds) {
            var d = self.getTokenExpirationDate();
            offsetSeconds = offsetSeconds || 0;
            if (d === null) {
                return false;
            }

            // Token expired?
            return !(d.valueOf() > (new Date().valueOf() + (offsetSeconds * 1000)));
        };

        self.isAuthorized = function () {
            return Enums.TOKEN in localStorage;
        };

        return self;
    }

})();
