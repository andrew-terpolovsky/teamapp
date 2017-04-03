import factory

import random

from doiq.accounts.models import User
from doiq.chat.models import Chat
from doiq.channel.models import Channel, ChannelMembership
from faker import Factory

FAKER = Factory.create()


class UserFactory(factory.django.DjangoModelFactory):
    full_name = factory.LazyAttribute(lambda x: FAKER.name())
    email = factory.LazyAttribute(lambda x: FAKER.email())
    username = factory.LazyAttribute(lambda x: FAKER.user_name())
    password = factory.PostGenerationMethodCall('set_password', 'secret')

    class Meta:
        model = User
        django_get_or_create = ('email',)


class ChannelFactory(factory.django.DjangoModelFactory):
    owner = factory.LazyAttribute(lambda x: UserFactory())
    name = factory.LazyAttribute(lambda x: FAKER.word())
    description = factory.LazyAttribute(lambda x: FAKER.text(200))

    class Meta:
        model = Channel
        django_get_or_create = ('name', )

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of members were passed in, use them
            for member in extracted:
                ChannelMembership.objects.create(channel=self, member=member)


class ChatFactory(factory.django.DjangoModelFactory):
    sender = factory.LazyAttribute(lambda x: UserFactory())
    channel = factory.LazyAttribute(lambda x: ChannelFactory())
    message = factory.LazyAttribute(
        lambda x: FAKER.text(random.randint(10, 200)))

    class Meta:
        model = Chat
