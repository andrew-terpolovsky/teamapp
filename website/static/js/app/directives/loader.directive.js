/*
 * Directive shows loader on global event or loading rootScope variable status
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('progressLoader', progressLoader);

    progressLoader.$inject = ['$rootScope'];

    function progressLoader($rootScope) {
        return {
            restrict: 'C',
            template: '<div class="loader-wrapper"><svg class="ripple-svg" viewBox="0 0 60 60" version="1.1" xmlns="http://www.w3.org/2000/svg"><circle class="first-circle" cx="30" cy="30" r="24"></circle><circle class="middle-circle" cx="30" cy="30" r="24"></circle></svg></div>',
            link: function (scope, element) {
                $rootScope.$watch('loading', function (newValue) {
                    if (newValue) {
                        element.delay(100).fadeIn();
                    }
                    else {
                        element.stop(true, false).fadeOut();
                    }
                });
            }
        }
    }
})();
