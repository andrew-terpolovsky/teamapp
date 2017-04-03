/*
 * Directive provide title for project pages in <head>.
 * Title is taken from params of ui-router directive.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('scrollbarMacosx', scrollbarMacosx)
        .directive('scrollbarInner', scrollbarInner);

    scrollbarMacosx.$inject = ['$timeout', 'uuid4'];
    scrollbarInner.$inject = ['$timeout'];

    function scrollbarMacosx($timeout, uuid4) {
        return {
            restrict: 'C',
            link: function (scope, element, attrs) {
                scope.scroll_id = attrs.scrollId || uuid4.generate();
                scope.scroll_top_lock = null;
                $timeout(function () {
                    element.scrollbar({
                        "onScroll": function (y, x, q, w, e) {
                            if (y.scroll === 0) {
                                if (scope.scroll_top_lock) return;
                                scope.scroll_top_lock = $timeout(function () {
                                    scope.$applyAsync(function () {
                                        scope.$broadcast('scroll:top', scope.scroll_id);
                                        $timeout.cancel(scope.scroll_top_lock);
                                        scope.scroll_top_lock = null;
                                    });
                                }, 400);
                            }
                        }
                    });
                });
            }
        }
    }

    function scrollbarInner($timeout) {
        return {
            restrict: 'C',
            link: function (scope, element) {
                $timeout(function () {
                    element.scrollbar();
                });
            }
        }
    }
})();
