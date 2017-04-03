(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('JsTZ', JsTZ);

    JsTZ.inject = ['$window'];

    function JsTZ($window) {
        return $window.jstz.determine();
    }
})();
