import datetime
import random
import logging

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import datastore_types


class Counter(object):
    """A counter using sharded writes to prevent contentions.

    Should be used for counters that handle a lot of concurrent use.
    Follows pattern described in Google I/O talk:
        http://sites.google.com/site/io/building-scalable-web-applications-with-google-app-engine

    Memcache is used for caching counts, although you can force
    non-cached counts.

    Usage:
        hits = Counter('hits')
        hits.increment()
        hits.get_count()
        hits.get_count(nocache=True)  # Forces non-cached count.
        hits.decrement()
    """
    MAX_SHARDS = 50

    def __init__(self, name, num_shards=5, cache_time=30):
        self.name = name
        self.num_shards = min(num_shards, Counter.MAX_SHARDS)
        self.cache_time = cache_time

    def delete(self):
        q = db.Query(CounterShard).filter('name =', self.name)
        # Need to use MAX_SHARDS since current number of shards
        # may be smaller than previous value.
        shards = q.fetch(limit=Counter.MAX_SHARDS)
        for shard in shards:
            shard.delete()

    def memcache_key(self):
        return 'Counter' + self.name

    def get_count(self, nocache=False):
        total = memcache.get(self.memcache_key())
        if nocache or total is None:
            total = 0
            q = db.Query(CounterShard).filter('name =', self.name)
            shards = q.fetch(limit=Counter.MAX_SHARDS)
            for shard in shards:
                total += shard.count
            memcache.add(self.memcache_key(), str(total),
                         self.cache_time)
            return total
        else:
            logging.debug("Using cache on %s = %s", self.name, total)
            return int(total)
    count = property(get_count)

    def increment(self):
        CounterShard.increment(self.name, self.num_shards)
        return memcache.incr(self.memcache_key())

    def decrement(self):
        CounterShard.increment(self.name, self.num_shards,
                               downward=True)
        return memcache.decr(self.memcache_key())

class CounterShard(db.Model):
    name = db.StringProperty(required=True)
    count = db.IntegerProperty(default=0)

    @classmethod
    def increment(cls, name, num_shards, downward=False):
        index = random.randint(1, num_shards)
        shard_key_name = 'Shard' + name + str(index)
        def get_or_create_shard():
            shard = CounterShard.get_by_key_name(shard_key_name)
            if shard is None:
                shard = CounterShard(key_name=shard_key_name,
                                     name=name)
            if downward:
                shard.count -= 1
            else:
                shard.count += 1
            key = shard.put()
        try:
            db.run_in_transaction(get_or_create_shard)
            return True
        except db.TransactionFailedError():
            logging.error("CounterShard (%s, %d) - can't increment",
                          name, num_shards)
            return False
