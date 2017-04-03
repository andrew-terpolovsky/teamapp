(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .controller('DashboardController', DashboardController);

    DashboardController.$inject = [
        '$scope', '$rootScope', '$state', '$uibModal', 'Models', 'Urls', 'Enums', 'Socket', 'Audio', 'toastr'
    ];

    function DashboardController($scope, $rootScope, $state, $uibModal, Models, Urls, Enums, Socket, Audio, Alert) {
        $scope.$on('$stateChangeSuccess', function (event, toState) {
            $scope.route = toState.name;
            $scope.route_ctrl = toState.controller;
        });

        $scope.createTask = function (channel_id) {
            $uibModal.open({
                size: 'md',
                resolve: {
                    task: function () {
                        return new Models.Tasks({
                            files: [],
                            due_date: '',
                            status: 0,
                            priority: 1,
                            related_channel: null
                        });
                    },
                    channel: channel_id
                },
                windowClass: 'side-modal',
                controller: 'ManageTaskController',
                templateUrl: Urls[Enums.TEMPLATES.TASKS.MANAGE]
            }).result.then(function (data) {
                $rootScope.$broadcast('tasks-changed');
                if (!$state.params.channelId) {
                    $state.go((data || {}).redirect_state || 'dashboard.tasks.my');
                }
            });
        };

        $scope.friendList = function () {
            $uibModal.open({
                size: 'sm',
                windowClass: 'side-modal',
                controller: 'FriendsListController',
                templateUrl: Urls[Enums.TEMPLATES.ACCOUNT.FRIENDS]
            })
        };

        $scope.closePrivateChat = function ($event, p_chat) {
            if ($event) {
                $event.stopPropagation();
                $event.stopImmediatePropagation();
                $event.preventDefault();
            }


            Models.Channel.close_private_chat({friend_id: p_chat.id}).$promise.then(function () {
                p_chat.private_channel_opened = false;
                if ($state.is('dashboard.channels.detail') && $state.$current.locals.globals.$stateParams.channelId == p_chat.private_channel_uid) {
                    $state.go('dashboard.tasks.my');
                }
            });
        };

        $scope.createChannel = function () {
            $uibModal.open({
                size: 'md',
                resolve: {
                    task: function () {
                        return new Models.Tasks({
                            files: [],
                            due_date: '',
                            status: 0,
                            priority: 1
                        });
                    },
                    owner: true
                },
                windowClass: 'side-modal',
                controller: 'ManageChannelCtrl',
                templateUrl: Urls[Enums.TEMPLATES.CHANNEL.MANAGE]
            }).result.then(function (channel) {
                    $state.go('dashboard.channels.detail', {channelId: channel.channel_uid});
                });
        };

        $scope.$watch(function () {
            return $rootScope.user.channels;
        }, function (n) {
            if (!n) return;
            var reserved_name = {};
            for (var i = 0; i < $rootScope.user.channels.length; i++) {
                if (!$rootScope.user.channels[i].orig_name) {
                    $rootScope.user.channels[i].orig_name = $rootScope.user.channels[i].name;
                }
                if (reserved_name[$rootScope.user.channels[i].orig_name] === undefined) {
                    reserved_name[$rootScope.user.channels[i].orig_name] = 1;
                } else {
                    reserved_name[$rootScope.user.channels[i].orig_name]++;
                    $rootScope.user.channels[i].name = $rootScope.user.channels[i].orig_name +
                    ' (' + reserved_name[$rootScope.user.channels[i].orig_name] + ')';
                }
            }

        }, true);

        $scope.stringAlphabeticalComparator = function (v1, v2) {

            if (v1.type == 'boolean') {
                if (v1.value == v2.value) return 0;
                return v1.value ? -1 : 1;
            }

            var vals = [v1.value.toLowerCase(), v2.value.toLowerCase()];
            vals.sort();
            return vals.indexOf(v1.value.toLowerCase()) == 0 ? -1 : 1;
        };

        $scope.getOpenedProperty = function (v) {

            return v.opened;
        };

        $scope.getNameProperty = function (v) {

            return v.name;
        };

        $scope.checkChannelExists = function (channel_uid) {

            var ch = $rootScope.user.channels.filter(function (ch) {
                return ch.channel_uid == channel_uid
            });
            if (!ch.length) return false;
            return ch[0];
        };

        $scope.checkPrivateChannelExists = function (data) {

            var f = $rootScope.user.private_chats.filter(function (f) {
                return f.private_channel_uid == data.channel_uid
            });
            if (!f.length) {
                var private_chat = {
                    active: false,
                    channel_uid: data.channel_uid,
                    counter_unread: 0,
                    email: data.sender.email,
                    full_name: data.sender.full_name,
                    id: data.sender.id,
                    image: data.sender.image,
                    private_channel_opened: false,
                    private_channel_uid: data.channel_uid,
                    username: data.sender.username
                };
                $rootScope.user.private_chats.push(private_chat);
                return private_chat;
            };
            return f[0];
        };

        $scope.receiveMessageListener = function (data) {
            data = JSON.parse(data);
            if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == data.channel_uid) {
                $rootScope.$broadcast('receive_message', data);
                Audio.play('notification_short');
            } else {
                if (data.channel_type == 2) {
                    var ch = $scope.checkChannelExists(data.channel_uid);
                    if (!ch) return;
                    ch.counter_unread += 1;
                } else if (data.channel_type == 1) {
                    var pch = $scope.checkPrivateChannelExists(data);
                    pch.private_channel_opened = true;
                    pch.counter_unread += 1;
                }
                Audio.play('notification_large');
            }
        };

        $scope.receiveFilesListener = function (data) {
            data = JSON.parse(data);
            if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == data.channel_uid) {
                $rootScope.$broadcast('receive_files', data);
                Audio.play('notification_short');
            } else {
                if (data.channel_type == 2) {
                    var ch = $scope.checkChannelExists(data.channel_uid);
                    if (!ch) return;
                    ch.counter_unread += 1;
                } else if (data.channel_type == 1) {
                    var pch = $scope.checkPrivateChannelExists(data);
                    //if (!pch) return;
                    pch.private_channel_opened = true;
                    pch.counter_unread += 1;
                }
                Audio.play('notification_large');
            }
        };

        $scope.receiveNotificationsListener = function (notification) {
            var ch, channel_index;
            notification = JSON.parse(notification);
            if (notification.type == 'kicked_member') {
                if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == notification.data.channel_uid) {
                    $rootScope.$broadcast('receive_notification', notification);
                    Audio.play('notification_short');
                } else {
                    if (notification.data.member_id != $rootScope.user.id) {
                        ch = $scope.checkChannelExists(notification.data.channel_uid);
                        if (!ch) return;
                        ch.counter_unread += 1;
                        Audio.play('notification_large');
                    } else {
                        ch = $scope.checkChannelExists(notification.data.channel_uid);
                        if (!ch) return;
                        channel_index = $rootScope.user.channels.indexOf(ch);
                        $rootScope.user.channels.splice(channel_index, 1);
                        $state.go('dashboard.tasks.my');
                        Alert.info('For some reasons you was kicked from the ' + notification.data.channel_name, {
                            allowHtml: true,
                            timeOut: 5000
                        });
                    }
                }
            }

            if (notification.type == 'friend_accept_invite') {
                $rootScope.$broadcast('receive_notification', notification);
                if (!$rootScope.user.friends.filter(function (f) {
                        return f.id == notification.data.id
                    }).length) {
                    $rootScope.user.friends.push(notification.data);
                } else {
                    return;
                }
                Socket.send('trigger_update_channels');
            }

            if (notification.type == 'channel_archived') {
                if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == notification.data.channel_uid) {
                    $rootScope.$broadcast('receive_notification', notification);
                    Audio.play('notification_short');
                } else {
                    ch = $scope.checkChannelExists(notification.data.channel_uid);
                    if (!ch) return;
                    channel_index = $rootScope.user.channels.indexOf(ch);
                    $rootScope.user.channels[channel_index].opened = false;
                    Alert.info('Channel ' + notification.data.name + ' is archived.', {
                        allowHtml: true,
                        timeOut: 5000
                    });
                }
            }

            if (notification.type == 'channel_ownership_changed') {
                if ($rootScope.user.id == notification.data.owner.id) {
                    Alert.info('You become an owner of a channel: ' + notification.data.name, {
                        allowHtml: true,
                        timeOut: 5000
                    });
                    if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == notification.data.channel_uid) {
                        $rootScope.$broadcast('receive_notification', notification);
                        //Audio.play('notification_short');
                    } else {
                        ch = $scope.checkChannelExists(notification.data.channel_uid);
                        if (ch) {
                            channel_index = $rootScope.user.channels.indexOf(ch);
                            $rootScope.user.channels[channel_index] = notification.data;
                        } else {
                            $rootScope.user.channels.push(notification.data)
                        }
                    }
                }
            }

            if (notification.type == 'friend_added_to_channel') {
                Alert.info('You have been added to channel ' + notification.data.name, {
                    allowHtml: true,
                    timeOut: 5000
                });
                Audio.play('notification_large');
                var channel = $rootScope.user.channels.filter(function (c) {
                    return c.channel_uid == notification.data.channel_uid
                });
                if (!channel.length) {
                    notification.data.counter_unread = 0;
                    $rootScope.user.channels.push(notification.data);
                }
            }

            if (notification.type == 'member_added_to_channel') {
                $rootScope.$broadcast('receive_notification', notification);
            }

            if (notification.type == 'profile_changed' || notification.type == 'channel_tasks_modified') {
                //if ($state.current.name == 'dashboard.channels.detail') {
                $rootScope.$broadcast('receive_notification', notification);

                if (notification.data.full_name) {
                    var required_friend = $rootScope.user.friends.filter(
                        function (f) {
                            return f.id == notification.data.user_id
                        }
                    );

                    if (required_friend.length) {
                        required_friend[0].full_name = notification.data.full_name
                    }

                    var required_private_chat = $rootScope.user.private_chats.filter(
                        function (f) {
                            return f.id == notification.data.user_id
                        }
                    );

                    if (required_private_chat.length) {
                        required_private_chat[0].full_name = notification.data.full_name
                    }
                }
                //}
            }

            if (notification.type == 'file_binded_state_in_channel') {
                if ($state.current.name == 'dashboard.channels.detail' && $state.$current.locals.globals.$stateParams.channelId == notification.data.channel_uid) {
                    $rootScope.$broadcast('receive_notification', notification);
                }
            }

        };

        Socket.bindEventListener('receive_message', $scope.receiveMessageListener);
        Socket.bindEventListener('receive_files', $scope.receiveFilesListener);
        Socket.bindEventListener('receive_notification', $scope.receiveNotificationsListener);

    }

})();
