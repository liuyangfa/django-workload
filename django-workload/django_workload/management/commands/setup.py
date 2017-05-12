import string
import random
import unicodedata

from datetime import datetime, timedelta
from itertools import cycle

from cassandra.util import uuid_from_time
from django.core.management.base import BaseCommand, CommandError
from django_cassandra_engine.management.commands import sync_cassandra

from django_workload.models import UserModel, FeedEntryModel

_latin_chars = map(chr, range(256))
_latin_letters = [c for c in _latin_chars if unicodedata.category(c) == 'Ll']
# weighted random; mostly ascii with some latin
_letters_source = string.ascii_lowercase * 9 + ''.join(_latin_letters)


def random_string(min_length=5, max_length=30, title=False):
    """A random string consisting of Latin letters, optionally title-cased"""
    result = ''.join([random.choice(_letters_source)
                      for _ in range(random.randint(min_length, max_length))])
    return result if not title else result.title()


def random_datetime_generator(start=-1000, end=0):
    """Generator to produce an endless series of random datetime objects.

    *start* and *end* are relative values in number of days from today 00:00,
    and this generator produces random timestamps that fall between the two
    extremes (inclusive).
    """
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start, end = today + timedelta(days=start), today + timedelta(days=end)
    start, end = start.timestamp(), end.timestamp()

    while True:
        random_ts = random.uniform(start, end)
        yield datetime.fromtimestamp(random_ts)


class Command(BaseCommand):
    help = 'Set up the django workload database'

    def handle(self, **options):
        print('Running syncdb for Cassandra')
        sync_cassandra.Command().execute(**options)

        spinner = cycle('|/-\\')

        print('Creating 1000 random users')
        users = []
        user_ids = []
        for i in range(10**3):
            print('\r{} {}'.format(next(spinner), i), end='')
            user = UserModel(name=random_string(title=True))
            user.save()
            users.append(user)
            user_ids.append(user.id)
        print('\r      ', end='\r')

        print('Creating following relationships between these users')
        for i, user in enumerate(users):
            print('\r{} {}'.format(next(spinner), i), end='')
            followers = random.sample(user_ids, random.randrange(50))
            user.following = [uuid for uuid in followers if user.id != uuid]
            user.save()
        print('\r      ', end='\r')

        print('Creating 100k random feed entries')
        feedids = map(uuid_from_time, random_datetime_generator())
        for i in range(10**4):
            print('\r{} {}'.format(next(spinner), i), end='')
            entry = FeedEntryModel(
                userid=random.choice(user_ids), id=next(feedids),
                comment_count=random.randrange(10))
            entry.save()
        print('\r       ', end='\r')
