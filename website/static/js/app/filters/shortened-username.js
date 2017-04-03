(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .filter('short_name', shortName);

    shortName.$inject = [];

    function shortName() {
        return function (name) {
            if (!name) return '';
            var parts = name.split(' ');
            parts = parts.map(function (p) {return p.charAt(0).toUpperCase();}).slice(0, 2);
            return parts.join('');
        }
    }

})();