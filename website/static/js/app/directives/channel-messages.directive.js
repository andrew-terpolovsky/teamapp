/*
 * Directive chat messages.
 * Takes channel params to filter channel messages.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('channelMessages', channelMessages)
        .directive('textMessage', textMessage)
        .directive('fileMessage', fileMessage)
        .directive('notificationMessage', notificationMessage)
        .directive('compileMessage', compileMessage);

    channelMessages.$inject = [
        '$timeout', '$window', '$q', '$uibModal', 'toastr', 'Models'
    ];
    textMessage().$inject = ['$timeout', '$compile', 'Models'];
    fileMessage.$inject = ['$timeout', '$compile', 'Models'];

    function channelMessages($timeout, $window, $q, $uibModal, toastr, Models) {
        return {
            restrict: 'EA',
            scope: false,
            templateUrl: '/static/templates/views/channels/messages.html',
            link: function (scope, element, attrs) {
                var $el = $(element),
                    params = {
                        page: 1,
                        count: 10
                    };
                scope.wrapped_element = angular.element(element);
                scope.container = scope.wrapped_element.parents('.chat-scroll-wrapper');
                scope.messages_loaded_promise = $q.defer();
                scope.messages_loaded_counter = 0;
                scope.stick_history_to_bottom_initial = true;
                scope.ignored_further_history_load_on_scroll_init = false;
                scope.last_message_id = null;
                scope.messages = [];

                scope.$on('receive_notification', function (event, notification) {

                    if (notification.type == 'profile_changed') {

                        for (var i = 0; i < scope.messages.length; i ++) {
                            if (scope.messages[i].sender && scope.messages[i].sender.id == notification.data.user_id) {
                                if (notification.data.avatar) scope.messages[i].sender.image = notification.data.avatar;
                                if (notification.data.full_name) scope.messages[i].sender.full_name = notification.data.full_name;
                            }
                        }
                    }

                });

                scope.$on('scroll:top', function ($event, scroll_id) {

                    if (scope.scroll_id == scroll_id) {
                        if (!scope.ignored_further_history_load_on_scroll_init) {
                            scope.ignored_further_history_load_on_scroll_init = true;
                            return;
                        }
                        if (!scope.messages.length == 0 && !scope.loading) {
                            //scope.messages[scope.messages.length - 1].last = true;
                            //scope.$applyAsync(function () {
                            //    scope.ready_to_load_promise.resolve();
                            //});
                            scope.ready_to_load_promise.resolve();
                        }
                    }
                });

                scope.$applyAsync(function () {
                    load();
                    scope.creteReady2LoadPromise();
                });

                scope.creteReady2LoadPromise = function () {

                    scope.ready_to_load_promise = $q.defer();
                    scope.ready_to_load_promise.promise
                        .then(
                        function () {

                            var poll_message_exists = function (poll_message_exists_promise, class_) {

                                $timeout(function () {

                                    if (angular.element(class_).size()) {
                                        poll_message_exists_promise.resolve();
                                    } else {
                                        return poll_message_exists(poll_message_exists_promise, class_);
                                    }
                                }, 500);
                            };
                            var wait_for_oldest_message_id_promise = $q.defer();
                            scope.container.css('overflow', 'hidden !important');
                            load(wait_for_oldest_message_id_promise);

                            wait_for_oldest_message_id_promise.promise.then(function (oldest_id) {
                                var poll_message_exists_promise = $q.defer();
                                poll_message_exists(poll_message_exists_promise, '.msg' + oldest_id);
                                poll_message_exists_promise.promise.then(function () {
                                    if (scope.last_message_id) {
                                        scope.container.scrollTop(scope.container.find('.msg' + scope.last_message_id)[0].offsetTop);
                                        //scope.container.css('overflow', 'scroll !important');
                                        scope.last_message_id = null;
                                        $timeout(scope.creteReady2LoadPromise, 1000);
                                    }
                                });
                            });
                            //alert(1);

                        }
                    );

                };

                function load(wait_for_oldest_message_id_promise) {
                    //var flag_last_message_calculated = false;
                    if (params.page === null) return;
                    scope.loading = true;
                    params.channel = scope.channel.id;
                    var oldest_message_id = null;
                    Models.Chat.query(params, function (messages) {
                        params.page = messages.next_page;
                        if (params.page === null) {
                            scope.ignored_further_history_load_on_scroll_init = true;
                        }
                        var messages = messages.results;
                        for (var i = 0; i < messages.length; i++) {
                            if (!messages[i].message && messages[i].files) continue;
                            //messages[i].message = scope.markSafe(messages[i].message);
                        }
                        if (wait_for_oldest_message_id_promise) {
                            oldest_message_id = messages[messages.length - 1].id;
                            wait_for_oldest_message_id_promise.resolve(oldest_message_id);
                        }

                        if (scope.messages.length) {
                            scope.last_message_id = scope.messages[scope.messages.length - 1].id;
                        }
                        scope.messages = scope.messages.concat(messages);
                        if (!scope.last_message_id && scope.messages.length) {
                            scope.last_message_id = scope.messages[scope.messages.length - 1].id;
                        }

                        scope.loading = false;
                    });

                }

                scope.messages_loaded_promise.promise
                    .then(
                    null,
                    null,
                    function () {

                        scope.messages_loaded_counter += 1;
                        if (scope.messages_loaded_counter == scope.messages.length) {
                            var content_height = scope.wrapped_element.height();
                            scope.$applyAsync(function () {
                                if (scope.stick_history_to_bottom_initial) {
                                    scope.stick_history_to_bottom_initial = false;
                                    scope.container.scrollTop(content_height);
                                }
                                if (scope.container.data().scrollbar.scrolly.maxScrollOffset - scope.container.scrollTop() <= 50) {
                                    scope.container.scrollTop(content_height);
                                }

                            })
                        }
                    }
                );
            }
        }
    }

    function textMessage($timeout, $window, Models) {
        return {
            restrict: 'E',
            scope: false,
            templateUrl: '/static/templates/views/channels/text-message.html',
            link: function (scope, element, attrs) {
                scope.messages_loaded_promise.notify();
            }
        }
    }

    function fileMessage($timeout, $window, Models) {
        return {
            restrict: 'E',
            scope: false,
            templateUrl: '/static/templates/views/channels/file-message.html',
            link: function (scope, element, attrs) {
                scope.messages_loaded_promise.notify();
            }
        }
    }

    function notificationMessage($timeout, $window, Models) {
        return {
            restrict: 'E',
            scope: false,
            templateUrl: '/static/templates/views/channels/notification-message.html',
            link: function (scope, element, attrs) {
                scope.messages_loaded_promise.notify();
            }
        }
    }

   function compileMessage($compile, $parse, wdtEmoji) {
       return {
           restrict: 'A',
           link: function (scope, element, attr) {
               scope.$watch(attr.content, function () {
                   element.html(wdtEmoji.render($parse(attr.content)(scope)));
                   $compile(element.contents())(scope);
               }, true);
           }
       }
   }
})();
