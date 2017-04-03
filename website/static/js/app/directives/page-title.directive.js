/*
 * Directive provide title for project pages in <head>.
 * Title is taken from params of ui-router directive.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('pageTitle', pageTitle);

    pageTitle.$inject = ['$rootScope'];

    function pageTitle($rootScope) {
        return {
            template: "{{title}}",
            link: function (scope) {
                scope.titleWatcher = function (event, toState) {
                    scope.title = 'DO IQ | ';
                    if (toState.data && toState.data.pageTitle) scope.title += toState.data.pageTitle;
                };
                $rootScope.$on('$stateChangeStart', scope.titleWatcher);
            }
        }
    }
})();
