(function () {
    'use strict';

    angular
        .module('DoIqApp.routes', [])
        .config(configRoutes);

    configRoutes.$inject = ['$stateProvider', '$urlRouterProvider'];

    /**
     * @name config
     * @desc Define valid application routes
     */
    function configRoutes($stateProvider, $urlRouterProvider, Urls, Enums) {
        $stateProvider
        // home page routing
            .state('home', {
                //abstract: true,
                templateUrl: '/static/templates/layouts/home.html',
                controller: 'HomeController',
                data: {
                    pageTitle: 'Welcome',
                    allow_any: true
                }
            })
            .state('home.sign-in', {
                url: '/:email',
                templateUrl: '/static/templates/views/accounts/sign-in.html',
                controller: 'SignInController',
                data: {
                    pageTitle: 'Sign In',
                    allow_any: true
                }
            })
            .state('home.sign-up', {
                url: '/sign-up/{invite_signature:(?:.+/)?}',
                templateUrl: '/static/templates/views/accounts/sign-up.html',
                controller: 'SignUpController',
                resolve: {
                    invitation: function ($rootScope, $stateParams, $http, $q, $state, AuthService, Socket, toastr) {

                        if (!$stateParams.invite_signature) return {};
                        var deferred = $q.defer();
                        $http.post('/api/accept-invite/' + $stateParams.invite_signature).then(function (response) {

                            if (response.data.jwt_token && !response.data.channel && !response.data.friend) {
                                AuthService.setToken(response.data.jwt_token);
                                Socket.bindListeners();
                                $state.go('dashboard.tasks.my');
                                return;
                            }
                            if (response.data.jwt_token && (response.data.channel || response.data.friend)) {
                                //AuthService.setToken(response.data.jwt_token);
                                $rootScope.forceGetUser(response.data.jwt_token).then(function () {

                                    Socket.bindListeners();

                                    if (response.data.friend) {
                                        var fr = $rootScope.user.friends.filter(function (f) {
                                            return f.id == response.data.friend.id
                                        });
                                        if (!fr.length) {
                                            $rootScope.user.friends.push(response.data.friend);
                                        } else {
                                            //$rootScope.user.friends.filter(function (f) {
                                            //    return f.id == response.data.friend.id
                                            //})[0].private_channel_uid = response.data.friend.private_channel_uid;
                                        }
                                    }

                                    if (response.data.channel) {
                                        var ch = $rootScope.user.channels.filter(function (ch) {
                                            return ch.channel_uid == response.data.channel.channel_uid
                                        });
                                        if (!ch.length) {
                                            $rootScope.user.channels.push(response.data.channel);
                                        }
                                        $state.go('dashboard.channels.detail', {channelId: response.data.channel.channel_uid});
                                        return;
                                    }
                                    $state.go('dashboard.tasks.my');
                                });
                                return;
                            }
                            deferred.resolve(response.data);
                        }, function () {
                            toastr.error('Invitation is expired.', 'Error!');
                            deferred.resolve();
                        });
                        return deferred.promise;
                    }
                },
                data: {
                    pageTitle: 'Sign Up',
                    allow_any: true
                }
            })
            .state('home.activate', {
                url: '/activate/{token_signature:(?:.+/)?}',
                templateUrl: '/static/templates/views/accounts/sign-in.html',
                controller: 'SignUpController',
                resolve: {
                    invitation: function ($rootScope, $stateParams, $http, $q, $state, AuthService, Socket) {

                        if (!$stateParams.token_signature) return {};
                        var deferred = $q.defer();
                        $http.post('/api/complete-sign-up/' + $stateParams.token_signature).then(function (response) {

                            if (response.data.jwt_token && !response.data.channel && !response.data.friend) {
                                AuthService.setToken(response.data.jwt_token);
                                Socket.bindListeners();
                                $state.go('dashboard.tasks.my');
                                return;
                            }
                            deferred.resolve(response.data);
                        });
                        return deferred.promise;
                    }
                },
                data: {
                    pageTitle: 'Sign Up',
                    allow_any: true
                }
            })
            .state('home.logout', {
                url: '/logout/',
                templateUrl: '/static/templates/views/accounts/logout.html',
                controller: 'LogoutController',
                data: {
                    pageTitle: 'Logout',
                    allow_any: true
                }
            })
            .state('home.forgot-password', {
                url: '/forgot-password/',
                templateUrl: '/static/templates/views/accounts/forgot-password.html',
                controller: 'ForgotPasswordController',
                data: {
                    pageTitle: 'Forgot Password',
                    allow_any: true
                }
            })
            //workspace routing
            .state('dashboard', {
                //abstract: true,
                templateUrl: '/static/templates/layouts/dashboard.html',
                controller: 'DashboardController',
                data: {
                    pageTitle: 'Dashboard'
                }
            })
            .state('dashboard.profile', {
                url: '/profile/',
                templateUrl: '/static/templates/views/accounts/profile.html',
                controller: 'ProfileController',
                data: {
                    pageTitle: 'Profile Settings'
                }
            })
            .state('dashboard.invite', {
                url: '/invitations/',
                templateUrl: '/static/templates/views/accounts/invite.html',
                controller: 'InviteController',
                data: {
                    pageTitle: 'Invite Others'
                }
            })
            .state('dashboard.chats', {
                abstract: true,
                url: '/chats/',
                template: '<div class="ui-view view-animation" />',
                data: {
                    pageTitle: 'Chats'
                }
            })
            .state('dashboard.chats.detail', {
                url: ':friendId/',
                templateUrl: '/static/templates/views/chats/chat.html',
                controller: 'ChatController',
                resolve: {
                    current_channel: function ($rootScope, $stateParams, $q, Models) {

                        var current_channel_promise = $q.defer();
                        $rootScope.user.$promise.then(function () {
                            if ($stateParams.channelId) {
                                Models.Channel.get({id: $stateParams.channelId}, function (channel) {

                                    current_channel_promise.resolve(channel);
                                });
                            }
                        });

                        return current_channel_promise.promise;
                    }
                },
                data: {
                    pageTitle: 'Private Chat'
                }
            })
            .state('dashboard.tasks', {
                abstract: true,
                url: '/tasks/',
                template: '<div class="ui-view view-animation" />',
                data: {
                    pageTitle: 'Tasks'
                }
            })
            .state('dashboard.tasks.my', {
                url: 'my/',
                templateUrl: '/static/templates/views/tasks/my-list.html',
                controller: 'MyTasksController',
                data: {
                    pageTitle: 'My Tasks'
                }
            })
            .state('dashboard.tasks.team', {
                url: 'team/',
                templateUrl: '/static/templates/views/tasks/team-list.html',
                controller: 'TeamTasksController',
                data: {
                    pageTitle: 'Team Tasks'
                }
            })
            .state('dashboard.tasks.archived', {
                url: 'archived/',
                templateUrl: '/static/templates/views/tasks/archived-list.html',
                controller: 'ArchivedTasksController',
                data: {
                    pageTitle: 'Archived Tasks'
                }
            })
            .state('dashboard.channels', {
                abstract: true,
                url: '/channels/',
                template: '<div class="ui-view view-animation" />',
                data: {
                    pageTitle: 'Channels'
                }
            })
            .state('dashboard.channels.detail', {
                url: '{channelId:[a-zA-Z0-9-]+}/',
                templateUrl: '/static/templates/views/channels/channel.html',
                controller: 'ChannelController',
                resolve: {
                    current_channel: function ($rootScope, $stateParams, $q, Models) {

                        var current_channel_promise = $q.defer();
                        $rootScope.user.$promise.then(function () {
                            if ($stateParams.channelId) {
                                Models.Channel.get({id: $stateParams.channelId}, function (channel) {

                                    current_channel_promise.resolve(channel);
                                });
                            }
                        });

                        return current_channel_promise.promise;
                    }
                },
                onEnter: function ($timeout, $state, current_channel) {

                    //if (!current_channel.opened) {
                    //    $timeout(function () {
                    //
                    //        $state.go('dashboard.tasks.my')
                    //    });
                    //}
                },
                data: {
                    pageTitle: 'Channel'
                }
            })
            .state("home.otherwise", {
                url: "/404/",
                templateUrl: "/static/templates/views/core/404.html",
                controller: 'PageNotFoundController',
                data: {
                    pageTitle: 'Page Not Found'
                }
            });

        $urlRouterProvider.otherwise('/404/');
    }
})();
