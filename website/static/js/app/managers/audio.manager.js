(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('Audio', AudioManager);

    AudioManager.$inject = ['$rootScope', '$window', '$timeout', '$q', 'ngAudio', 'uuid4'];

    function AudioManager($rootScope, $window, $timeout, $q, ngAudio, uuid4) {

        var api = {};
        api.sounds = {
             'notification_large': ngAudio.load('/static/audio/arpeggio.ogg'),
             'notification_short': ngAudio.load('/static/audio/hit.ogg')
        };

        api.play = function (notification) {

            notification = notification || 'notification_large';
            api.sounds[notification].play();
        };

        return api;
    }

})();
