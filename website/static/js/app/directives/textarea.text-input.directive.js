/*
 * Directive chat messages.
 * Takes channel params to filter channel messages.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('textareaInput', textareaInputDirective);

    textareaInputDirective.$inject = ['$timeout', '$window', '$q', 'Models'];

    function textareaInputDirective($timeout, $window, $q, Models) {
        return {
            restrict: 'E',
            scope: false,
            template: '<textarea ng-keypress="keyboardPress($event)"></textarea>',
            replace: true,
            link: function (scope, element, attrs) {

                scope.typing = false;
                scope.typing_timer_promise = null;

                scope.keyboardPress = function ($event) {

                    if (($event.keyCode == 13 || $event.keyCode == 10) && ($event.ctrlKey || $event.metaKey || $event.shiftKey)) {
                        $event.preventDefault();
                        $event.stopImmediatePropagation();
                        scope.saveSelection();
                        scope.insertAtCaret('\r\n');
                    } else if (scope.keyboardPressOuter && ($event.keyCode == 13 || $event.keyCode == 10)) {
                        scope.keyboardPressOuter($event);
                    } else if (!($event.keyCode == 13 || $event.keyCode == 10)) {
                        scope.typing = true;
                        if (scope.typing_timer_promise) {
                            $timeout.cancel(scope.typing_timer_promise);
                        }
                        scope.typing_timer_promise = $timeout(function () {

                            scope.typing = false;
                        }, 1500);
                    }
                };

                scope.saveSelection = function () {

                    element.data('lastSelection', element.getSelection());
                };

                element.focusout(scope.saveSelection);

                element.bind("beforedeactivate", function () {

                    scope.saveSelection();
                    element.unbind("focusout");
                });

                scope.insertAtCaret = function (text) {
                    var selection = element.data('lastSelection');
                    element.focus();
                    element.setSelection(selection.start, selection.end);
                    element.replaceSelectedText(text);
                }
            }
        }
    }

})();
