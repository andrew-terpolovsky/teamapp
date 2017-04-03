(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .controller('ProfileController', ProfileController);

    ProfileController.$inject = ['$scope', '$rootScope', 'toastr', 'Models', 'FileManager'];

    function ProfileController($scope, $rootScope, Alert, Models, FileManager) {
        $scope.profileImg = {};
        $scope.timezones = Models.GetTZ.query();

        $scope.updateAvatar = function (file) {
            $scope.profileImg = {
                'background-image': 'url(' + (file ? file : '/static/img/profile.png') + ')'
            }
        };

        $rootScope.user.$promise.then(function () {
            $scope.profile = $rootScope.user;
            $scope.updateAvatar($scope.profile.get_picture_medium);

            $scope.update = function () {
                $scope.profile.errors = [];
                $scope.profile.$save().then(function (res) {
                    Alert.success('Profile has been updated successfully');
                }, function (response) {
                    $scope.profile.errors = response.data;
                    Alert.error('Profile update failed. Please check for form errors.');
                })
            };
        });

        $scope.fileUploaded = function (data) {
            $scope.updateAvatar(data.files[0].file);
            $scope.profile.image = data.files[0].id;
        };

        $scope.uploadAvatar = function () {
            FileManager.openFileManager('personal', $scope.fileUploaded);
        };
    }
})();
