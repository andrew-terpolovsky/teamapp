import random
from optparse import make_option

from django.core.management.base import BaseCommand
from doiq.accounts.models import User
from doiq.channel.models import Channel
from doiq.utils import factories as f


class Command(BaseCommand):
    """
    Generate fake data into the DB
    """
    can_import_settings = True

    option_list = BaseCommand.option_list + (

        make_option('--message', '-m',
                    action='store',
                    dest='chat',
                    default=10,
                    help='number of chat messages to create'),

        make_option('--channel', '-c',
                    action='store',
                    dest='channel',
                    default=1,
                    help='number of channel'),

        make_option('--friends', '-f',
                    action='store',
                    dest='friends',
                    default=2,
                    help='number of friends'),

        make_option('--owner', '-o',
                    action='store',
                    dest='owner',
                    help='existing user email'),
    )

    def handle(self, *args, **options):
        nb_chat = int(options['chat'])
        nb_channel = int(options['channel'])
        nb_friends = int(options['friends'])
        self.owner = options['owner']

        if nb_friends and nb_friends > 0:
            self.stdout.write("\n Creating %d friends \n" % nb_friends)
            self.create_friends(nb_friends)

        if nb_channel and nb_channel > 0:
            self.stdout.write("\n Creating %d channels \n" % nb_channel)
            self.create_channels(nb_channel)

        if nb_chat and nb_chat > 0:
            self.stdout.write("\n Creating %d chats \n" % nb_chat)
            self.create_chats(nb_chat)

    def create_channels(self, number):
        owner = self._get_owner()
        for i in range(number):
            members = User.objects.all()
            c = f.ChannelFactory(owner=owner, members=members)
            self.stdout.write("---> Created  %s" % (c))

    def create_friends(self, number):
        for i in range(number):
            u = f.UserFactory()
            self._get_owner().friends.add(u)
            self.stdout.write("---> Created  %s" % (u))

    def create_chats(self, number):
        for i in range(number):
            f.ChatFactory(sender=self._get_user(), channel=self._get_channel())

    def _get_owner(self):
        if self.owner:
            return User.objects.get(email=self.owner)

    def _get_user(self):
        return random.choice(User.objects.all())

    def _get_channel(self):
        return random.choice(Channel.objects.all())
