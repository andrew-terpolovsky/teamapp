(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .controller('FindImageInFilesCtrl', FindImageInFilesCtrl)
        .controller('TasksBaseController', TasksBaseController)
        .controller('ManageTaskController', ManageTaskController)
        .controller('MyTasksController', MyTasksController)
        .controller('TeamTasksController', TeamTasksController)
        .controller('ArchivedTasksController', ArchivedTasksController)
        .controller('ChannelTasksListCtrl', ChannelTasksListCtrl);

    FindImageInFilesCtrl.$inject = [
        '$scope', '$filter'
    ];
    TasksBaseController.$inject = [
        '$scope', '$rootScope', '$uibModal', '$controller', 'Models', 'Enums', 'Urls'
    ];
    ManageTaskController.$inject = [
        '$scope', '$rootScope', '$filter', '$state', 'Models', '$uibModal', '$uibModalInstance', 'FileManager', 'toastr',
        'Urls', 'Enums'
    ];
    MyTasksController.$inject = [
        '$scope', '$rootScope', '$controller'
    ];
    TeamTasksController.$inject = [
        '$scope', '$rootScope', '$controller', 'Models'
    ];
    ArchivedTasksController.$inject = [
        '$scope', '$rootScope', '$controller', 'Models'
    ];
    ChannelTasksListCtrl.$inject = [
        '$scope', '$controller', '$q', '$uibModal', 'Models', 'Urls', 'Enums'
    ];

    /**
     * @name FindImageInFilesCtrl
     * @desc Controller which help to detect image in files with findFile function
     */
    function FindImageInFilesCtrl($scope, $filter) {
        $scope._findResult = function (item) {
            if (item.content_type && item.content_type.substr(0, 5) == "image") {
                return item;
            }
        };

        $scope.findFile = function (item) {
            if (item.files && item.files.length) {
                var f = $filter('filter')(item.files, $scope._findResult);
                if (f.length) {
                    item.preview = 'url(' + f[0]['file'] + ')';
                }
            }
            return item;
        };
    }

    /**
     * @name TasksBaseController
     * @desc Base controller for tasks section which can be nested by other controllers.
     */
    function TasksBaseController($scope, $rootScope, $uibModal, $controller, Models, Enums, Urls) {
        $controller('FindImageInFilesCtrl', {$scope: $scope});
        $rootScope.loading = true;
        $scope.today = new Date();
        $scope.empty = true;
        $scope.filter = {
            by: '-created',
            private: 1
        };
        $scope.titles = {0: 'DO', 1: 'DELEGATE', 2: 'DELAY', 3: 'DONE'};

        $scope.filter_options = {
            'assignee__full_name': 'Assignee',
            '-created': 'Date created',
            '-due_date': 'Due date'
        };

        $scope.defineTaskScope = function (task) {
            var k;
            if (task.done) {
                k = 3
            }
            else if (new Date().getTime() < new Date(task.due_date).getTime() - 45 * 24 * 60 * 60 * 1000) {
                k = 2
            }
            else if (task.assignee && $rootScope.user.id != task.assignee.id) {
                k = 1
            }
            else {
                k = 0
            }
            return k;
        };

        $scope.loadTasks = function () {
            Models.Tasks.query($scope.filter).$promise.then(function (data) {
                $scope.group_task = {};
                $scope.empty = true;
                angular.forEach(data, function (item) {
                    var k = $scope.defineTaskScope(item);
                    if (!$scope.group_task[k]) {
                        $scope.group_task[k] = [];
                    }
                    $scope.group_task[k].push($scope.findFile(item));
                    $scope.empty = false;
                });
                $rootScope.loading = false;
            });
        };

        $scope.filterBy = function (by) {
            $scope.filter.by = by;
            $scope.loadTasks();
        };

        $rootScope.$on('tasks-changed', function () {
            $scope.loadTasks();
        });

        $scope.saveCallback = function (data, tasks, $index, key) {
            if (data) {
                var k = $scope.defineTaskScope(data);
                var item = $scope.findFile(data);
                if (k == key) {
                    tasks[$index] = item;
                }
                else {
                    tasks.splice($index, 1);
                    if (!$scope.group_task[k]) {
                        $scope.group_task[k] = [];
                    }
                    $scope.group_task[k].unshift(item);
                }
            }
            else {
                tasks.splice($index, 1);
            }
        };

        $scope.openTask = function (tasks, $index, key) {
            $uibModal.open({
                size: 'lg',
                resolve: {
                    task: function () {
                        return angular.copy(tasks[$index])
                    }
                },
                windowClass: 'side-modal',
                controller: 'ManageTaskController',
                templateUrl: Urls[Enums.TEMPLATES.TASKS.MANAGE]
            }).result.then(function (data) {
                $scope.saveCallback(data, tasks, $index, key);
            });
        };
    }

    /**
     * @name MyTasksController
     * @desc My tasks page controller, manage list of my tasks.
     */
    function MyTasksController($scope, $rootScope, $controller) {
        $controller('TasksBaseController', {$scope: $scope});
        $rootScope.user.$promise.then(function () {
            $scope.loadTasks();
        });
    }

    /**
     * @name TeamTasksController
     * @desc Team tasks page controller, manage list of channel tasks.
     */
    function TeamTasksController($scope, $rootScope, $controller, Models) {
        $controller('TasksBaseController', {$scope: $scope});

        $scope.filter = {
            by: '-created',
            my_channel_tasks: true
        };

        $scope.saveCallback = function (data, tasks, $index) {
            if (data) {
                tasks[$index] = $scope.findFile(data);
            }
            else {
                tasks.splice($index, 1);
            }
        };

        $scope.loadTasks = function () {
            Models.Tasks.query($scope.filter).$promise.then(function (data) {
                $scope.group_task = {};
                $scope.empty = true;
                angular.forEach(data, function (item) {
                    var k = item.related_channel_name;
                    if (!$scope.group_task[k]) {
                        $scope.group_task[k] = [];
                    }
                    $scope.group_task[k].push($scope.findFile(item));
                    $scope.empty = false;
                });
                $rootScope.loading = false;
            });
        };

        $rootScope.user.$promise.then(function () {
            $scope.loadTasks();
        });
    }

    /**
     * @name ArchivedTasksController
     * @desc Archived tasks page controller, manage list of channel tasks.
     */
    function ArchivedTasksController($scope, $rootScope, $controller, Models) {
        $controller('TasksBaseController', {$scope: $scope});

        $scope.filter = {
            by: '-created',
            archived: 1
        };

        $scope.loadTasks = function () {
            Models.Tasks.query($scope.filter).$promise.then(function (data) {
                $scope.group_task = {};
                $scope.empty = true;
                angular.forEach(data, function (item) {
                    var k = item.related_channel_name || 'my tasks';
                    if (!$scope.group_task[k]) {
                        $scope.group_task[k] = [];
                    }
                    var task = $scope.findFile(item);
                    task.done = true;
                    task.deleted = true;
                    $scope.group_task[k].push(task);
                    $scope.empty = false;
                });
                $rootScope.loading = false;
            });
        };

        $rootScope.user.$promise.then(function () {
            $scope.loadTasks();
        });
    }

    function ManageTaskController($scope, $rootScope, $filter, $state, Models, $uibModal, $uibModalInstance, FileManager, Alert, Urls, Enums) {
        $scope.channels = $filter('filter')($rootScope.user.channels, {type: 2, opened: true});
        $scope.fields_params = {};
        $scope.priorities = [
            {name: 'Low', index: 0},
            {name: 'Normal', index: 1},
            {name: 'Medium', index: 2},
            {name: 'High', index: 3}
        ];
        $scope.statuses = [
            {name: 'Not Started', index: 0},
            {name: 'In-progress', index: 1},
            {name: 'Stopped', index: 2},
            {name: 'Completed', index: 3}
        ];
        $scope.datePickerOptions = {
            minDate: new Date()
        };
        $scope.picker_opened = false;
        $scope.friends = Models.Friends.query();
        $scope.task = $scope.$resolve.task;

        $scope.changeChannel = function () {
            $scope.fields_params.channel = $scope.task.related_channel.channel_uid;
            $scope.friends = Models.Friends.query($scope.fields_params);
        };

        if ($scope.task.due_date) {
            $scope.task.due_date = new Date($scope.task.due_date);
        }

        if (!$scope.task.status.index) {
            $scope.task.status = $filter('filter')($scope.statuses, {index: $scope.task.status}, true)[0];
        }

        if (!$scope.task.priority.index) {
            $scope.task.priority = $scope.priorities[$scope.task.priority];
        }

        if ($scope.task.related_channel) {
            $scope.task.related_channel = $filter('filter')($scope.channels, {id: $scope.task.related_channel}, true)[0];
            $scope.changeChannel();
        } else if ($scope.$resolve.channel) {
            $scope.channel_task = true;
            $scope.task.related_channel = $filter('filter')($scope.channels, {channel_uid: $scope.$resolve.channel}, true)[0];
            $scope.changeChannel();
        }

        $scope.owner = $scope.task.owner ? $rootScope.user.id == $scope.task.owner.id : true;

        $scope.setupActivity = function () {
            $scope.activities = Models.Activity.query({task: $scope.task.id});
            $scope.activity = new Models.Activity();
            $scope.activity.task = $scope.task.id;
        };

        $scope.updateAvatar = function (file) {
            return {
                'background-image': 'url(' + (file ? file : '/static/img/profile.png') + ')'
            }
        };

        $scope.sendActivity = function () {
            $scope.activity.$save().then(function (data) {
                $scope.activities.unshift(data);
                $scope.activity = new Models.Activity();
                $scope.activity.task = $scope.task.id;
            }, function (response) {
                $scope.activity.errors = response.data;
            });
        };

        $scope.openDatePicker = function () {
            $scope.picker_opened = true;
        };

        $scope.receiveFiles = function (data) {
            var current_ids = $scope.task.files.map(function (file) {
                return file.id;
            });
            for (var i in data.files) {
                var file = data.files[i];

                if (current_ids.indexOf(file.id) == -1) {
                    $scope.task.files.push(file);
                }
            }
        };

        $scope.addFiles = function () {
            FileManager.openFileManager('personal', $scope.receiveFiles);
        };

        $scope.deleteTask = function () {
            $uibModal.open({
                size: 'sm',
                resolve: {
                    name: function () {
                        return $scope.task.name
                    },
                    action: function () {

                        return 'archive';
                    },
                },
                windowClass: 'side-modal',
                controller: 'DeleteItemCtrl',
                templateUrl: Urls[Enums.TEMPLATES.CORE.DELETE]
            }).result.then(function (data) {
                $scope.task.$remove().then(function () {
                    $uibModalInstance.close(false);
                    Alert.success("Task archived successfully");
                }, function (errors) {
                    $scope.task.errors = errors.data;
                    Alert.error("Task cannot be deleted. Please try again later.");
                });
            });
        };

        $scope.deleteFile = function ($index) {
            $scope.task.files.splice($index, 1);
        };

        $scope.deleteComment = function (comment, $index) {
            $uibModal.open({
                size: 'sm',
                resolve: {
                    action: function () {

                        return 'delete';
                    },
                    name: function () {
                        return 'comment'
                    }
                },
                windowClass: 'side-modal',
                controller: 'DeleteItemCtrl',
                templateUrl: Urls[Enums.TEMPLATES.CORE.DELETE]
            }).result.then(function (data) {
                comment.$remove().then(function () {
                    $scope.activities.splice($index, 1);
                });
            });
        };

        $scope.saveTask = function () {
            var task = angular.copy($scope.task);
            if (task.status.index !== undefined) {
                task.status = task.status.index;
            }
            if (task.priority.index !== undefined) {
                task.priority = task.priority.index;
            }
            if (task.related_channel) {
                task.related_channel = task.related_channel.id;
            }
            if (task.status == 1 && !task.assignee) {
                task.assignee = {id: $rootScope.user.id};
            }
            task.$save().then(function (res) {
                var method = $scope.task.id ? 'updated' : 'created';
                Alert.success("Task has successfully " + method, "");
                res.redirect_state = $state.current.name;
                $uibModalInstance.close(res);
            }, function (errors) {
                $scope.task.errors = errors.data;
                Alert.error("Form is invalid. Please fix errors and try again", "");
            });
        };

        $scope.isDelete = function () {
            var del = false;
            var t = $scope.task;
            if (t.id && !t.deleted) {
                if ((t.assignee && t.owner && t.assignee.id == t.owner.id) || t.done || !t.assignee) {
                    del = true;
                }
            }
            return del;
        };

        $scope.getSingleDownloadLink = function (file_id) {
            return 'http://' + location.hostname + ':9999/download-message-file/' + localStorage.getItem(Enums.TOKEN) + '/-/' + file_id + '/';
        };

        if ($scope.task.id) {
            $scope.setupActivity();
        }
    }


    function ChannelTasksListCtrl($scope, $controller, $q, $uibModal, Models, Urls, Enums) {
        $controller('FindImageInFilesCtrl', {$scope: $scope});
        $scope.channel = $scope.$resolve.channel;
        $scope.tasks_loaded_promise = null;
        if ($scope.$resolve.task_id) {
            $scope.tasks_loaded_promise = $q.defer();
            $scope.tasks_loaded_promise
                .promise
                .then(
                function () {

                    var $index = -1;
                    for (var i = 0; i <= $scope.tasks.length; i ++ ) {
                        if ($scope.tasks[i].id == $scope.$resolve.task_id) {
                            $index = i;
                            break;
                        }
                    }
                    $scope.openTask($scope.tasks[$index], $index);
                }
            );
        }

        $scope.filterTasksByAssignee = function (el, i, array) {

            if ($scope.filterTasksByAssignee.assignee_filter) {
                if (el.assignee && $scope.filterTasksByAssignee.assignee_filter.id == el.assignee.id) return true;
            } else return true;
            return false;
        };

        $scope.updateAvatar = function (file) {
            return {
                'background-image': 'url(' + (file ? file : '/static/img/profile.png') + ')'
            }
        };

        Models.Tasks.query({channel: $scope.channel.id}).$promise.then(function (data) {
            $scope.tasks = data;
            if ($scope.tasks_loaded_promise) {
                $scope.tasks_loaded_promise.resolve();
            }
            for (var i in $scope.tasks) {
                $scope.findFile($scope.tasks[i]);
            }
        });

        $scope.openTask = function (task, $index) {
            var new_task = false;

            if (!task) {
                new_task = true;
                task = new Models.Tasks({
                    files: [],
                    due_date: '',
                    status: 0,
                    priority: 1,
                    related_channel: null
                });
            }

            $uibModal.open({
                size: 'md',
                resolve: {
                    task: angular.copy(task),
                    channel: function () {
                        return $scope.channel.channel_uid
                    }
                },
                windowClass: 'side-modal',
                controller: 'ManageTaskController',
                templateUrl: Urls[Enums.TEMPLATES.TASKS.MANAGE]
            }).result.then(function (data) {
                $scope.tasks[$index] = data;
                if (!data) {
                    $scope.tasks.splice($index, 1);
                }
                else {
                    var item = $scope.findFile(data);
                    if (new_task) {
                        $scope.tasks.unshift(item);
                    }
                }
            });
        };
    }

})();