(function () {
    'use strict';

    angular
        .module('DoIqApp')
        .controller('InviteController', InviteController)
        .controller('ChannelInviteController', ChannelInviteController);

    InviteController.$inject = ['$scope', '$state', '$rootScope', 'toastr', 'Models'];
    ChannelInviteController.$inject = ['$scope', '$rootScope', 'Models', 'toastr', '$uibModalInstance'];


    function InviteController($scope, $state, $rootScope, Alert, Models) {
        $scope.filter_options = {
            '-created': 'Creation Date',
            'email': 'Assignee',
            'accepted': 'Status'
        };
        $scope.filter = {
            by: '-created'
        };

        $scope.vm = {
            invite: {invited_by: $scope.user.id},
            invites: []
        };

        $scope.filterBy = function (field) {
            $scope.filter.by = field;
            $scope.fetchInvites();
        };

        $scope.updateAvatar = function (user) {
            var file = (user && user.image) ? user.image : null;
            return {
                'background-image': 'url(' + (file ? '/media/' + file : '/static/img/profile.png') + ')'
            }
        };

        $scope.fetchInvites = function () {
            Models.Invite.query($scope.filter).$promise.then(function (response) {
                $scope.vm.invites = response;
            });
        };

        $scope.sendInvite = function (invite) {
            Models.Invite.send(invite, function (response) {
                if (response.flag_invite_yourself) {
                    Alert.warning('You are not allowed to invite yourself.', 'Warning!');
                } else if (response.flag_invite_already_exists) {
                    Alert.warning('Invite is already exists.', 'Warning!');
                } else if (response.flag_invite_already_friend) {
                    if (response.flag_invite_already_friend == 1) Alert.warning('Friend exists.', 'Warning!');
                    if (response.flag_invite_already_friend != 1) Alert.warning('Friends exist.', 'Warning!');
                } else {
                    Alert.success("Invite has successfully sent", 'Success!');
                }
                $scope.vm.invite.emails = [];
                $scope.fetchInvites();
            }, function (err) {
                Alert.error("Sending invite failed. Please try again!", 'Error!');
            })
        };

        $scope.delete = function (invite, $index) {
            invite.$delete({id: invite.id}, function (response) {
                $scope.vm.invites.splice($index, 1);
                Alert.info("Invite has been removed", 'Info!');
            }, function (err) {
                Alert.error(err.data, 'Error!');
            })
        };

        $scope.resend = function (invite) {
            Models.Invite.resend(invite, function (response) {
                Alert.success("Invite has successfully re-sent", 'Success!');
            }, function (err) {
                Alert.error("Sending invite failed. Please try again!", 'Error!');
            })
        };

        $scope.deleteFriend = function (invite, index) {

            $rootScope.user.$friend_delete({friend_id: invite.user.id, action: 'friend_delete'})
                .then(function () {

                    $scope.vm.invites.splice(index, 1);
                });
        };

        $scope.openPrivateChat = function (invite) {

            Models.Channel.open_private_chat({friend_id: invite.user.id}).$promise
                .then(function (response) {

                    var friend_ = $rootScope.user.friends.filter(function (f) {
                        return f.id == invite.user.id;
                    });
                    if (friend_.length) {
                        friend_[0].private_channel_uid = response.channel_uid;
                        friend_[0].private_channel_opened = true;
                    }
                    $state.go('dashboard.channels.detail', {channelId: response.channel_uid});
                    var private_chat = $rootScope.user.private_chats.filter(function (p) {
                        return p.id == invite.user.id
                    });
                    if (!private_chat.length) {
                        $rootScope.user.private_chats.push({
                            counter_unread: 0,
                            private_channel_opened: true,
                            private_channel_uid: response.channel_uid,
                            username: invite.user.username,
                            id: invite.user.id
                        })
                    } else {
                        private_chat[0].private_channel_opened = true;
                    }
                });
        };

        $scope.more = function (invite) {

        };

        $scope.fetchInvites();

        $scope.$on('receive_notification', function (event, notification) {

            if (notification.type == 'friend_accept_invite') {
                var invitation_exists = $scope.vm.invites.filter(function (i) {

                    return i.email == notification.data.email;
                });
                if (!invitation_exists.length) return;
                invitation_exists[0].accepted = true;
                invitation_exists[0].user = notification.data;
            }
        });
    };

    function ChannelInviteController($scope, $rootScope, Models, Alert, $uibModalInstance) {

        $scope.invite = $scope.$resolve.invite;
        $scope.wait_invite_somebody_lock = false;
        $scope.all_joined_friends = [];

        $scope.sendInvite = function () {

            $scope.wait_invite_somebody_lock = true;

            //var selected_friend_emails = $scope.friends.filter(function (f) {
            //    return f.selected;
            //}).map(function (f) {
            //    return f.email;
            //});
            var selected_friend_ids = $scope.friends.filter(function (f) {
                return f.selected;
            }).map(function (f) {
                return f.id;
            });

            //var invite_emails = $scope.invite.emails || '';
            //invite_emails = invite_emails.split(',').filter(function (e) {
            //    return e.length > 0;
            //});
            //invite_emails = invite_emails.map(function (e) {
            //    return e.trim();
            //});

            //for (var i = 0; i < selected_friend_emails.length; i++) {
            //    if (invite_emails.indexOf(selected_friend_emails[i]) == -1) {
            //        invite_emails.push(selected_friend_emails[i]);
            //    }
            //}
            var invite_data = angular.copy($scope.invite);
            //invite_data.emails = invite_emails.join(',');
            invite_data.ids = selected_friend_ids;

            Models.Invite.send(invite_data, function (response) {

                $scope.wait_invite_somebody_lock = false;
                if (response.flag_invite_yourself) {
                    Alert.warning('You are not allowed to invite yourself.', 'Warning!');
                } else if (response.flag_invite_already_exists) {
                    Alert.warning('Invite is already exists.', 'Warning!');
                } else if (response.flag_invite_already_friend) {
                    if (response.flag_invite_already_friend == 1) Alert.warning('Friend exists.', 'Warning!');
                    if (response.flag_invite_already_friend != 1) Alert.warning('Friends exist.', 'Warning!');
                } else if (response.emails_sent == 0 && !selected_friend_ids.length) {
                    Alert.warning('Empty emails.', 'Warning!');
                } else {
                    Alert.success("Invite has successfully sent", 'Success!');
                }

                if (response.new_members.length) {

                    var members = $scope.friends.filter(function (f) {
                        return response.new_members.indexOf(f.id) > -1;
                    });

                    for (var i = 0; i < members.length; i++) {
                        if ($scope.all_joined_friends.indexOf(members[i].id) == -1) {
                            $scope.all_joined_friends.push(members[i].id)
                        }
                    }

                    $scope.$resolve.friend_add_callback.call({}, $scope.all_joined_friends);
                    $scope.all_joined_friends = [];
                }

                $scope.invite.emails = '';
            }, function (err) {
                $scope.invite.errors = err.data;
                Alert.error("Sending invite failed. Please try again!", 'Error!');
            })
        };

        $scope.closeDialog = function () {

            if ($scope.wait_invite_somebody_lock) {
                $timeout(function () {
                    $scope.closeDialog();
                }, 100);
                return;
            }
            $uibModalInstance.close();
        };

        $scope.$watchGroup([
                function () {

                    return $rootScope.user.friends;
                },
                '$resolve.channel.members'
            ],
            function (n, o) {
                var all_members_ids = n[1].map(function (m) {
                    return m.id
                });
                $scope.friends = n[0].filter(function (f) {
                    return all_members_ids.indexOf(f.id) == -1;
                })
            }
        );
    }

})();
