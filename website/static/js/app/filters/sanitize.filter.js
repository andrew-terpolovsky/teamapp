(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .filter("sanitize", sanitize);

    sanitize.$inject = ['$sce'];

    function sanitize($sce) {
        return function (htmlCode) {
            return $sce.trustAsHtml(htmlCode);
        }
    }

})();




