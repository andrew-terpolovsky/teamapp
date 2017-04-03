(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .provider('socket', function () {
            var default_options = {};

            this.setOptions = function (options) {
                default_options = options;
            };

            this.$get = function () {
                return {
                    getOptions: function () {
                        return default_options;
                    }
                };
            };
        })
        .factory('Socket', SocketManager);

    SocketManager.$inject = ['$rootScope', '$window', '$timeout', '$q', 'socket', 'uuid4', 'AuthService', 'Enums'];

    function SocketManager($rootScope, $window, $timeout, $q, socket, uuid4, AuthService, Enums) {

        var api = {};
        var appOptions = socket.getOptions();
        var hostname = $window.location.protocol + '//' + $window.location.hostname;
        var default_options = {
            socket_base_url: hostname + ':9999/chat',
            fail_retry: 500
        };
        api.interacting_promises = {};
        api.event_callbacks = {};
        api.listeners = {};
        api.pending = [];
        api.connected = false;
        api.connected_promise = $q.defer();
        api.locked = false;
        api.online_statuses = false;
        api.missed_heartbeat_promise = null;

        var options = angular.extend(default_options, appOptions);

        api.getPromiseUid = function () {

            return uuid4.generate();
        };

        api.ping = function () {

            api.send('king')
                .promise
                .then(function () {

                    if (api.missed_heartbeat_promise) {
                        $timeout.cancel(api.missed_heartbeat_promise);
                    }
                    api.missed_heartbeat_promise = $timeout(function () {

                        api.socket_sockj.close();
                    }, 10 * 1000);
                    $timeout(api.ping, 5 * 1000);
                });
        };

        api.bindListeners = function () {
            if (api.locked) $timeout(function () {
                api.bindListeners();
            }, 500);

            if (api.connected) return;

            api.locked = true;
            if (api.socket_sockj) {
                api.socket_sockj.close();
                delete api.socket_sockj;
            }
            api.socket_sockj = new SockJS(options.socket_base_url);

            api.socket_sockj.send = function (event, kwargs, past_acknowledge, no_ack) {

                if (kwargs && (typeof kwargs != 'object' || (typeof kwargs == 'object' && kwargs.constructor != Object))) {
                    throw Error('Support only hashes.')
                }

                var acknowledge = null;
                if (!no_ack) {
                    acknowledge = past_acknowledge || api.getPromiseUid();
                    var cur_deffered = $q.defer();
                    api.interacting_promises[acknowledge] = cur_deffered;
                }
                var event_struct = {
                    event: event || null,
                    kwargs: kwargs || {},
                    acknowledge: acknowledge
                };

                if (api.socket_sockj.readyState !== 1) {
                    api.pending.push(event_struct);
                } else {
                    var on_air = SockJS.prototype.send.call(api.socket_sockj, JSON.stringify(event_struct));
                }
                return cur_deffered;
            };

            api.socket_sockj.onopen = function () {

                api.connected = true;
                if (!$rootScope.$$phase) {
                    $rootScope.$applyAsync(function () {

                        api.connected_promise.notify(true);
                    });
                } else {
                    api.connected_promise.notify(true);
                }

                api.bindEventListener('online_statuses', function (data) {

                    api.online_statuses = JSON.parse(data);
                });

                api.send('authorize', {tokenJWT: AuthService.getToken()})
                    .promise
                    .then(function () {

                        api.pending.reverse();
                        while (api.pending.length && api.socket_sockj.readyState === 1) {
                            var pending = api.pending.pop();
                            api.socket_sockj.send(pending.event, pending.kwargs, pending.acknowledge);
                        }
                    })
                    .then(function () {
                        var listeners = api.listeners['connection_opened'];
                        if (listeners && listeners.length) {
                            angular.forEach(listeners, function (cb, i) {
                                if (!$rootScope.$$phase) {
                                    $rootScope.$applyAsync(function () {

                                        cb();
                                    });
                                } else {
                                    cb();
                                }
                            });
                        }
                    })
                    .then(function () {
                        //api.ping();
                    });
            };

            api.socket_sockj.onmessage = function (response) {
                if (response.type == 'message' && response.data.type == 'message') {
                    var deffered = api.interacting_promises[response.data.acknowledge];
                    if (deffered) {
                        $rootScope.$apply(function () {

                            deffered.resolve(response.data.result);
                            delete api.interacting_promises[response.data.acknowledge];
                        });
                    }
                    var event_callbacks = api.event_callbacks[response.data.event];
                    if (event_callbacks && event_callbacks.length) {
                        angular.forEach(api.event_callbacks[response.data.event], function (cb, i) {

                            $rootScope.$apply(function () {

                                cb(response.data.result);
                            });
                        });
                    }
                } else if (response.type == 'message' && response.data.type == 'event') {
                    var listeners = api.listeners[response.data.event];
                    if (listeners && listeners.length) {
                        angular.forEach(listeners, function (cb, i) {

                            $rootScope.$apply(function () {

                                var ack_promise = $q.defer();
                                cb(response.data.data, ack_promise);
                                var acknowledge = response.data.acknowledge;
                                ack_promise.promise.then(function (ack_response) {

                                    api.send('ack_callback', ack_response, acknowledge);
                                });
                            });
                        });
                    }
                }
            };

            api.socket_sockj.onclose = function (metadata) {
                api.connected = false;
                api.unbindEventListener('online_statuses');

                if (!AuthService.isAuthorized()) {
                    return;
                }
                $timeout(function () {

                    api.bindListeners();
                }, options.fail_retry);
            };

            api.locked = false;
        };

        api.send = function (event, kwargs, past_acknowledge, no_ack) {

            var deffered = api.socket_sockj.send(event, kwargs, past_acknowledge, no_ack);
            return deffered;
        };

        api.registerCallback = function (event, cb) {

            if (!api.event_callbacks[event]) {
                api.event_callbacks[event] = [];
            }
            api.event_callbacks[event].push(cb);
        };

        api.bindEventListener = function (event, listener) {

            if (!api.listeners[event]) {
                api.listeners[event] = [];
            }
            api.listeners[event].push(listener);
        };

        api.unbindEventListener = function (event, listener) {

            if (!api.listeners[event]) return;
            if (listener && api.listeners[event].indexOf(listener) != -1) {
                api.listeners[event].splice(api.listeners[event].indexOf(listener), 1);
            }
            if (!listener) {
                api.listeners[event] = [];
            }
        };

        api.close = function () {

            if (api.connected) {
                api.socket_sockj.close();
            }
        };

        return api;
    }

})();
