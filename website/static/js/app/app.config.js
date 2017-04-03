(function () {
    'use strict';

    angular
        .module('DoIqApp', [
            'DoIqApp.templates',
            'ui.router',
            'ui.select',
            'ui.bootstrap',
            'ngResource',
            'ngCookies',
            'ngAnimate',
            'ngSanitize',
            'ngTagsInput',
            'ngAudio',

            'DoIqApp.resource',
            'DoIqApp.routes',

            'toastr',
            'uuid4',
            'angularMoment',
            'monospaced.elastic'
        ])
        .config(configApp)
        .run(runApp);

    configApp.$inject = [
        '$interpolateProvider', '$httpProvider', '$locationProvider',
        'tagsInputConfigProvider', 'wdtEmojiProvider'
    ];

    runApp.$inject = [
        '$rootScope', '$state', '$timeout', 'Models', 'AuthService', 'Socket'
    ];

    function configApp($interpolateProvider, $httpProvider, $locationProvider, tags, emoji) {
        $httpProvider.defaults.headers.common['X-Requested-With'] = "XMLHttpRequest";
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.interceptors.push('authInterceptor');
        $httpProvider.defaults.useXDomain = true;
        $interpolateProvider.startSymbol("{[");
        $interpolateProvider.endSymbol("]}");
        $locationProvider.html5Mode(true);

        emoji.defaults.type = 'twitter';
        emoji.defaults.emojiType = 'twitter';
        emoji.defaults.emojiSheets.twitter = '/static/img/emoji/sheet_twitter_64.png';

        for (var k in wdtEmojiBundle.defaults.emojiSheets) {
            var image = new Image();
            image.src = wdtEmojiBundle.defaults.emojiSheets[k];
        }

        tags
            .setDefaults('tagsInput', {
                addOnEnter: true,
                minLength: 2,
                replaceSpacesWithDashes: false
            })
            .setDefaults('autoComplete', {
                maxResultsToShow: 7,
                debounceDelay: 0,
                loadOnFocus: true,
                loadOnEmpty: true,
                minLength: 1
            })
            .setActiveInterpolation('tagsInput', {
                placeholder: true,
                addOnEnter: true,
                removeTagSymbol: true
            })
            .setTextAutosizeThreshold(15);
    }

    function runApp($rootScope, $state, $timeout, Models, AuthService, Socket, Enums) {

        $rootScope.forceGetUser = function (token) {
            if (AuthService.isAuthorized()) {
                if (!$rootScope.user) {
                    $rootScope.user = new Models.SelfModel.get();
                    return $rootScope.user.$promise;
                }
                return $rootScope.user.$promise;
            }
            else if (token) {
                AuthService.setToken(token);
                return $rootScope.forceGetUser();
            }
            return null;
        };

        $rootScope.clearTokenInLocalStorage = function () {
            if (window.localStorage && 'DoIq.token' in window.localStorage) {
                delete window.localStorage['DoIq.token'];
            }
        };

        $rootScope.$on('unauthorized', function (event) {
            $timeout(function () {
                $rootScope.clearTokenInLocalStorage();
                $state.go('home.sign-in');
            }, 500);
        });

        $rootScope.$on('$stateChangeStart', function (event, toState) {
            if (AuthService.isAuthorized()) {
                if (!$rootScope.user) {
                    $rootScope.user = new Models.SelfModel.get();
                    $rootScope.user.$promise.then(function () {
                        Socket.bindListeners();
                    });
                }
                $rootScope.user.$promise.then(function () {
                    if (toState.data.allow_any && toState.name != 'home.logout') {
                        $state.go('dashboard.tasks.my');
                    }
                });
            }
            else {
                if (toState.data && !toState.data.allow_any) {
                    event.preventDefault();
                    $timeout(function () {
                        $rootScope.clearTokenInLocalStorage();
                        $state.go('home.sign-in');
                    });
                }
            }
        });

        $rootScope.loading = false;
    }
})();

