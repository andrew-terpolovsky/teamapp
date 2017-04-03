/*
 * Directive provide title for project pages in <head>.
 * Title is taken from params of ui-router directive.
 *
 * */

(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .directive('fileManager', FileManagerDirective);

    FileManagerDirective.$inject = ['$rootScope', '$timeout', '$q', 'FileManager'];

    function FileManagerDirective($rootScope, $timeout, $q, FileManager) {
        return {
            restrict: 'A',
            template: '',
            scope: {
                uploader_url: '=uploaderUrl',
                upload_callback: '&uploadCallback',
                upload_progress: '=uploadProgress'
            },
            link: function (scope, el, attr) {
                scope.inits = {};
                var local_options = {}, clickable, droppable;

                if (attr.fileManager) {
                    local_options = scope.$eval(attr.fileManager)
                }

                scope.initClickUploader = function (target) {
                    var uploader_options = local_options.uploader_options || {};
                    if (!FileManager.file_inputs[scope.$id]) {
                        var file_input = new mOxie.FileInput({
                            browse_button: target[0],
                            multiple: uploader_options.multiple || false,
                            accept: uploader_options.accept || "*/*"
                        });

                        file_input.onchange = function (e) {
                            var upload_deffered = scope.beforeUploading();
                            FileManager.handleUpload(scope.$id, 'b', upload_deffered);
                        };

                        file_input.oninit = function (e) {

                            file_input.refresh();
                        };

                        FileManager.file_inputs[scope.$id] = {
                            'file_input': file_input
                        };

                        $timeout(function () {

                            file_input.init();
                        }, 0);
                    }
                };

                scope.initDropUploader = function (target) {
                    $timeout(function () {
                        var uploader_options = local_options.uploader_options || {};
                        if (!FileManager.drop_zones[scope.$id]) {
                            var drop_zone = new mOxie.FileDrop({
                                drop_zone: target[0],
                                multiple: uploader_options.multiple || false,
                                accept: uploader_options.accept || "*/*"
                            });

                            drop_zone.ondrop = function (e) {
                                if ('preventDefault' in e) e.preventDefault();
                                if ('stopPropagation' in e) e.stopPropagation();

                                var upload_deffered = scope.beforeUploading();
                                FileManager.handleUpload(scope.$id, 'z', upload_deffered);
                            };

                            drop_zone.oninit = function (e) {
                                drop_zone.refresh();
                            };

                            FileManager.drop_zones[scope.$id] = {
                                'drop_zone': drop_zone
                            };

                            drop_zone.init();
                            scope.inits.drop = true;
                        }
                    }, 0);

                };

                scope.beforeUploading = function () {
                    var uploader_options = local_options.uploader_options || {};
                    scope.upload_deffered = $q.defer();
                    scope.upload_deffered.promise.then(
                        function (file_data) {
                            scope.upload_deffered = null;
                        },
                        null,
                        function (postback_data) {
                            if (postback_data.hasOwnProperty('progress')) {
                                scope.upload_progress = postback_data.progress;
                            } else {
                                scope.upload_callback.call(scope, {file: postback_data.response})
                            }

                        }
                    );

                    if (uploader_options.multiple) {
                        FileManager.uploader.setOption('multiple', uploader_options.multiple);
                    }

                    if (uploader_options.url) {
                        FileManager.uploader.setOption('url', uploader_options.url);
                    }
                    return scope.upload_deffered;
                };

                scope.$applyAsync(function () {
                    if (local_options.click) {
                        clickable = el[0].hasAttribute('fm-click-upload') ?
                            angular.element(el) : angular.element(el).find('[fm-click-upload]');

                        if (clickable) {
                            clickable.on('mouseover', function (e) {

                                scope.$apply(function () {

                                    scope.initClickUploader(clickable);
                                });
                                clickable.unbind('mouseover');
                            });

                        }
                    }

                    if (local_options.drop) {
                        droppable = el[0].hasAttribute('fm-drop-upload') ?
                            angular.element(el) : angular.element(el).find('[fm-drop-upload]');

                        if (droppable) {
                            droppable
                                .on('dragenter', function (e) {

                                    droppable.addClass('fm-state-dragenter');
                                    scope.$apply(function () {

                                        if (!scope.inits.drop) {
                                            scope.initDropUploader(droppable);
                                        }
                                    });
                                })
                                .on('dragleave', function (e) {
                                    droppable.removeClass('fm-state-dragenter');
                                })
                                .on('drop', function (e) {
                                    droppable.removeClass('fm-state-dragenter');
                                });

                        }
                    }
                });
            }
        }
    }
})();
