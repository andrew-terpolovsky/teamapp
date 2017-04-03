(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .provider('wdtEmoji', function () {

            //wdtEmojiBundle.defaults.emojiSheets.apple = './sheet_apple.png';
            //wdtEmojiBundle.defaults.emojiSheets.google = './sheet_google.png';
            wdtEmojiBundle.defaults.emojiSheets.twitter = './sheet_twitter.png';
            //wdtEmojiBundle.defaults.emojiSheets.emojione = './sheet_emojione.png';
            wdtEmojiBundle.defaults.type = 'twitter';
            wdtEmojiBundle.defaults.emojiType = 'twitter';

            this.defaults = wdtEmojiBundle.defaults;
            this.wdtEmojiBundle = wdtEmojiBundle;

            this.$get = function () {
                return wdtEmojiBundle;
            };
        })
        .directive('wdtEmoji', wdtEmojiDirective)
        .directive('newScope', newScope);

    wdtEmojiDirective.$inject = ['$rootScope', '$window', '$timeout', '$compile', '$templateCache', '$q', 'socket', 'uuid4', 'AuthService', 'Enums'];

    function newScope() {

        return {
            restrict: 'A',
            template: '',
            scope: true
        }
    }

    function wdtEmojiDirective($rootScope, $window, $timeout, $compile, $templateCache, $q, socket, uuid4, AuthService, Enums) {

        return {
            restrict: 'A',
            template: '',
            priority: 0,
            scope: {
                'emojiApiController': '='
            },
            terminal: true,
            link: function (scope, el, attrs) {

                scope.opened = false;
                scope.click_outside_binded = false;
                scope.id = angular.element(el).attr('id');
                if (!scope.id) {
                    scope.id = uuid4.generate();
                    angular.element(el).attr('id', scope.id);
                }
                angular.element('.page-content').append($compile($templateCache.get('/static/templates/views/channels/emoji-picker.html'))(scope));
                var api = wdtEmojiBundle.init('#' + scope.id, angular.element('#emoji-pick-icon')[0]);
                scope.emojiApiController = api;
                scope.emojiApiController.on('afterPickerOpen', function () {
                    scope.opened = true;
                    if (!scope.click_outside_binded) {
                        angular.element(document).on('click', 'html', scope.checkClickWithinEmojiPopup);
                    }
                    scope.click_outside_binded = true;

                    //scope.$apply();
                });

                scope.checkClickWithinEmojiPopup = function (e) {
                    if (scope.opened && !angular.element(e.target).parents('.wdt-emoji-popup').size()) {
                        scope.catchOutsideClick();
                    }
                };

                scope.catchOutsideClick = function () {
                    if (scope.opened) {
                        scope.emojiApiController.close();
                        scope.opened = false;
                        scope.click_outside_binded = false;
                        angular.element(document).off('click', 'html', scope.checkClickWithinEmojiPopup);
                        scope.$apply();
                    }
                };


                scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {

                    angular.element(document).off('click', 'html', scope.checkClickWithinEmojiPopup);
                });

            }
        }
    }

})();
