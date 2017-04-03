(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .factory('FileManager', FileManager)
        .controller('FileManagerBaseController', FileManagerBaseController);

    FileManagerBaseController.$inject = [
        '$scope', '$filter', '$q', '$timeout', '$uibModal', '$uibModalInstance', 'Urls', 'Enums', 'FileManagerResource', 'toastr'
    ];

    FileManager.$inject = [
        '$cookies', '$timeout', '$uibModal', 'Urls', 'Enums', 'FileManagerResource'
    ];

    function FileManagerBaseController($scope, $filter, $q, $timeout, $uibModal, $uibModalInstance, Urls, Enums, FileManagerResource, Alert) {
        $scope.query_params = $scope.$resolve.query_params || {};
        $scope.uploader_url = Urls[Enums.FILEMANAGER.SCOPE.PERSONAL.UPLOAD_ROOT];
        $scope.loading = false;
        $scope.selected_files = [];
        $scope.upload_progress = {bytes: 0, total: 0, percent: 0};

        FileManagerResource.list($scope.query_params).$promise.then(function (data) {
            $scope.files = data.list;
            $scope.files_searched = $scope.files;
            $scope.has_more = data.has_more;
            $scope.last_id = data.last_id;
        });

        $scope.addUploadedFile = function (file_data) {
            var file = JSON.parse(file_data.response);
            $scope.files.unshift(file);
            $scope.selectFile(file);
        };

        $scope.selectFile = function (file) {
            var index = $scope.selected_files.indexOf(file.id);
            if (index == -1) {
                file.selected = true;
                $scope.selected_files.push(file.id)
            }
            else {
                file.selected = false;
                $scope.selected_files.splice(index, 1);
            }
        };

        $scope.loadMoreFiles = function (newSearch) {
            if ($scope.loading) {
                $timeout(function () {
                    $scope.loadMoreFiles(newSearch);
                }, 500);
            }
            $scope.loading = true;

            var load_deffered = $q.defer();
            var params = {
                scope: $scope.$resolve.files_scope,
                last_id: $scope.last_id
            };
            params = angular.extend(params, $scope.query_params);
            if ($scope.searchQuery) {
                params.search_term = $scope.searchQuery;
            }
            if (newSearch) {
                params.last_id = -1;
            }
            FileManagerResource
                .list(params).$promise
                .then(function (files) {
                    if (newSearch) {
                        $scope.files = files.list;
                    } else {
                        $scope.files = $scope.files.concat(files.list);
                    }

                    $scope.files_searched = $scope.files;
                    $scope.has_more = files.has_more;
                    if (files.last_id) {
                        $scope.last_id = files.last_id;
                    }
                    $scope.loading = false;
                    load_deffered.resolve();
                });
            return load_deffered.promise;
        };

        $scope.deleteFiles = function () {
            if (!$scope.selected_files.length) return;
            $uibModal.open({
                size: 'sm',
                resolve: {
                    name: function () {

                        return 'selected files';
                    },
                    action: function () {

                        return 'delete';
                    },
                    bold: false
                },
                windowClass: 'side-modal',
                controller: 'DeleteItemCtrl',
                templateUrl: Urls[Enums.TEMPLATES.CORE.DELETE]
            }).result.then(function () {

                FileManagerResource.delete(null, {
                    scope: $scope.$resolve.files_scope,
                    files: $scope.selected_files
                }).$promise.then(
                    function (data) {

                        var undeleted_files = data.undeleted;
                        var undeleted_files_names = [];

                        for (var i = $scope.files.length - 1; i >= 0; i--) {
                            if (angular.element.inArray($scope.files[i].id, $scope.selected_files) != -1 &&
                                angular.element.inArray($scope.files[i].id, undeleted_files) == -1) {
                                $scope.files.splice(i, 1);
                            } else {
                                undeleted_files_names.push($scope.files[i].original_name);
                            }
                        }

                        if ($scope.files.length) {
                            $scope.last_id = $scope.files.reduce(function (a, b) {
                                return a.id > b.id ? a : b
                            }).id;
                        } else {
                            $scope.last_id = -1;
                        }

                        if (undeleted_files_names.length) {
                            Alert.info("Some files wasn't deleted: " + undeleted_files_names.join(', ') + '.', "");
                        } else {
                            Alert.info("Files deleted successfully", "");
                        }

                    }
                );
            });

        };

        $scope.getSingleDownloadLink = function (file_id) {
            return 'http://' + location.hostname + ':9999/download-message-file/' + localStorage.getItem(Enums.TOKEN) + '/-/' + file_id + '/';
        };

        $scope.$watch('searchQuery', function (n, o) {
            if (n) {
                /* If user fill search term ... */
                if (!o && !$scope.has_more) {
                    /* then if all files was loaded before, there no reasons to re-upload them ... */
                    //$scope.files_searched = $scope.files;
                } else {
                    /* else re-upload them */
                    $scope.loadMoreFiles(true)
                }
            } else {
                if (!n && o) {
                    /* If previous file set was filtered and now search term is empty then we could miss some files */
                    $scope.loadMoreFiles(true);
                }
            }
        });

        $scope.ok = function () {
            var files = $filter('filter')($scope.files, {selected: true});
            $uibModalInstance.close({
                files: files,
                ids: $scope.selected_files
            });
        }
    }

    function FileManager($cookies, $timeout, $uibModal, Urls, Enums) {
        var self = this;
        self.file_inputs = {};
        self.drop_zones = {};
        self.uploader = null;
        self.upload_deffered = null;

        self.openFileManager = function (fm_scope, callback, options) {

            self.uploader.settings.headers['Authorization'] = 'JWT ' + localStorage.getItem(Enums.TOKEN);

            options = options || {};
            var query_params = angular.extend({scope: fm_scope}, options.queryParams || {});
            var to_resolve = options.to_resolve || {};
            var resolve = {
                files_scope: function () {
                    return fm_scope;
                },
                query_params: function () {
                    return query_params;
                }
            };
            resolve = angular.extend(resolve, to_resolve);
            $uibModal.open({
                size: 'md',
                resolve: resolve,
                windowClass: 'side-modal',
                controller: options.controller || 'FileManagerBaseController',
                templateUrl: options.templateUrl || Urls[Enums.TEMPLATES.ACCOUNT.FILE_MANAGER]
            }).result.then(function (data) {
                if (callback) {
                    callback.call(this, data);
                }
            });
        };

        self.initUploader = function () {
            self.settings = {
                url: Urls[Enums.MODELS.CORE.UPLOAD],
                runtimes: 'html5,flash,silverlight,html4',
                browse_button: 'widely-used-uploader',
                flash_swf_url: '/static/bower_components/plupload/js/Moxie.swf',
                silverlight_xap_url: '/static/bower_components/plupload/js/Moxie.xap',
                filters: {
                    max_file_size: "20mb"
                },
                multipart_params: {},
                multipart: true,
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Authorization': 'JWT ' + localStorage.getItem(Enums.TOKEN),
                    'X-CSRFToken': $cookies.get("csrftoken")
                },
                resize: {
                    preserve_headers: false
                }
            };

            self.settings.init = {
                FilesAdded: function (up) {
                    up.start();
                },
                UploadProgress: function (up, file) {

                    self.upload_deffered.notify({
                        progress: {
                            percent: up.total.loaded / up.total.size,
                            bytes: up.total.loaded,
                            total: up.total.size
                        }
                    });
                },
                Error: function (up, err) {
                },
                FileUploaded: function (up, file, resp) {

                    self.upload_deffered.notify({response: resp});

                },
                UploadComplete: function (up, files) {

                    self.upload_deffered.resolve();
                    self.upload_deffered = null;

                    for (var i = files.length - 1; i >= 0; i--) {
                        up.removeFile(files[i])
                    }
                    up.total.reset();
                }
            };

            self.uploader = new plupload.Uploader(self.settings);
            self.uploader.init();
        };

        self.handleUpload = function (id, type, upload_deferred) {
            var file_source = (type == 'b' ? self.file_inputs : self.drop_zones)[id];
            self.upload_deffered = upload_deferred;
            self.uploader.addFile(
                file_source[type == 'b' ? 'file_input' : 'drop_zone'].files
            );
        };

        $timeout(self.initUploader);

        return self;
    }
})();
