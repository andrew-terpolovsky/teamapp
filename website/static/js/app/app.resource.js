(function () {
    'use strict';

    angular
        .module('DoIqApp.resource', [
            'ngResource'
        ])
        .factory('Resource', resourceFactory)
        .config(resourceConfig);


    resourceFactory.$inject = ['$resource'];
    resourceConfig.$inject = ['$httpProvider', '$resourceProvider'];

    function resourceFactory($resource) {
        return function (url, params, methods) {
            var defaults = {
                update: {method: 'put', isArray: false},
                query: {method: 'get', isArray: true},
                create: {method: 'post'}
            };

            methods = angular.extend(defaults, methods);

            var resource = $resource(url, params, methods);

            resource.prototype.$save = function (params, success, error) {
                if (!this.id) {
                    return this.$create(params, success, error);
                }
                else {
                    return this.$update(params, success, error);
                }
            };

            return resource;
        };
    }

    function resourceConfig($httpProvider, $resourceProvider) {

        $resourceProvider.defaults.stripTrailingSlashes = false;

        $httpProvider.interceptors.push(['$q', function ($q) {
            return {
                'request': function (request) {
                    return request;
                },

                'response': function (response) {
                    return response;
                },

                'requestError': function (rejection) {
                    return $q.reject(rejection);
                },

                'responseError': function (rejection) {
                    return $q.reject(rejection);
                }
            };
        }]);
    }

})();
