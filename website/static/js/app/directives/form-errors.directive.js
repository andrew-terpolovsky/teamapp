(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('formErrors', formErrors);

    function formErrors() {
        return {
            restrict: 'AE',
            scope: {
                'errors': '=formErrors'
            },
            template: "<ul><li ng-repeat='error in errors' ng-bind='error'></li></ul>",
            link: function(scope) {

            }
        }
    }

})();
