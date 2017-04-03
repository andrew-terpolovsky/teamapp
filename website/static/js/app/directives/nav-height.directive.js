/*
 * Directive provide title for project pages in <head>.
 * Title is taken from params of ui-router directive.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('navHeight', navHeight);

    function navHeight() {
        return {
            restrict: 'A',
            link: function(scope, element) {
                var scroll_height = element.innerHeight() - 295 - 61;
                var viewPortHeight = scroll_height / 2 - 63; // 63 - header height
                $('.chat-list-wrapper, .pm-list-wrapper').css("height", viewPortHeight + "px");
            }
        }
    }
})();
