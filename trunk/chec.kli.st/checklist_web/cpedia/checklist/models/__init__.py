import datetime
import random
import logging

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import datastore_types

from cpedia.pagination.GqlQueryPaginator import GqlQueryPaginator,GqlPage
from cpedia.pagination.paginator import InvalidPage,Paginator

import simplejson

def to_dict(model_obj, attr_list, init_dict_func=None):
    """Converts Model properties into various formats.

    Supply a init_dict_func function that populates a
    dictionary with values.  In the case of db.Model, this
    would be something like _to_entity().  You may also
    designate more complex properties in attr_list, like
      "counter.count"
    Each object in the chain will be retrieved.  In the
    example above, the counter object will be retrieved
    from model_obj's properties.  And then counter.count
    will be retrieved.  The value returned will have a
    key set to the last name in the chain, e.g. 'count'
    in the above example.
    """
    values = {}
    init_dict_func(values)
    for token in attr_list:
        elems = token.split('.')
        value = getattr(model_obj, elems[0])
        for elem in elems[1:]:
            value = getattr(value, elem)
        values[elems[-1]] = value
    if model_obj.is_saved():
        values['key'] =  str(model_obj.key())  
    return values

# Format for conversion of datetime to JSON
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

def replace_datastore_types(entity):
    """Replaces any datastore types in a dictionary with standard types.

    Passed-in entities are assumed to be dictionaries with values that
    can be at most a single list level.  These transformations are made:
      datetime.datetime      -> string
      db.Key                 -> key hash suitable for regenerating key
      users.User             -> dict with 'nickname' and 'email'
    TODO -- GeoPt when needed
    """
    def get_replacement(value):
        if isinstance(value, datetime.datetime):
            return value.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))
        elif isinstance(value, datetime.date):
            return value.strftime(DATE_FORMAT)
        elif isinstance(value, datetime.time):
            return value.strftime(TIME_FORMAT)
        elif isinstance(value, datastore_types.Key):
            return str(value)
        elif isinstance(value, users.User):
            return { 'nickname': value.nickname(),
                     'email': value.email(),
                     'user_id':value.user_id() }
        else:
            return None

    for key, value in entity.iteritems():
        if isinstance(value, list):
            new_list = []
            for item in value:
                new_value = get_replacement(item)
                new_list.append(new_value or item)
            entity[key] = new_list
        else:
            new_value = get_replacement(value)
            if new_value:
                entity[key] = new_value

class SerializableModel(db.Model):
    """Extends Model to have json and possibly other serializations

    Use the class variable 'json_does_not_include' to declare properties
    that should *not* be included in json serialization.
    TODO -- Complete round-tripping
    """
    json_does_not_include = []

    def to_json(self, attr_list=[]):
        def to_entity(entity):
            """Convert datastore types in entity to
               JSON-friendly structures."""
            self._to_entity(entity)
            for skipped_property in self.__class__.json_does_not_include:
                del entity[skipped_property]
            replace_datastore_types(entity)
        values = to_dict(self, attr_list, to_entity)
        #return simplejson.dumps(values)   #simplejson.dumps will be applied when do the rpc call.
        return values

class MemcachedModel(SerializableModel):
    #All the query to this model need to be self-stored.
    #The dict need to set a unique key, and the value must be db.Query() object.
    querys = {}
    page_querys = {}

    def delete_cached_list_page(self):
        memcache_list_keys = self.__class__.memcache_list_key()
        email = None
        if hasattr(self,"user") and self.user:
            user_id_ = self.user.user_id()
        memcache_page_keys = self.__class__.memcache_page_key(user_id=user_id_)
        if memcache_list_keys is not None and len(memcache_list_keys) > 0:
            memcache.delete_multi(memcache_list_keys)
        if memcache_page_keys is not None and len(memcache_page_keys) > 0:
            memcache.delete_multi(memcache_page_keys)

    def delete(self):
        super(MemcachedModel, self).delete()
        self.delete_cached_list_page()
        if self.is_saved():
            memcache.delete(self.__class__.memcache_object_key(self.key()))


    def put(self):
        key = super(MemcachedModel, self).put()
        self.delete_cached_list_page()
        memcache.set(self.__class__.memcache_object_key(key),self)
        return key

    @classmethod
    def get_or_insert(cls, key_name, **kwds):
        obj = super(MemcachedModel, cls).get_or_insert(key_name, **kwds)
        self.delete_cached_list_page()
        return obj

    @classmethod
    def memcache_list_key(cls):
        return [cls.__name__ +"_list_" +  query_key  for query_key in cls.querys]

    @classmethod
    def memcache_page_key(cls, user_id=None):
        if user_id is not None:
            user_id = "_"+user_id
        else:
            user_id = ""
        return [cls.__name__ +"_page_" + query_key + user_id  for query_key in cls.page_querys]

    @classmethod
    def memcache_object_key(cls,primary_key):
        return cls.__name__ + '_' + str(primary_key)

    @classmethod
    def get_cached(cls,primary_key,nocache=False):
        key_ = cls.__name__ + "_" + primary_key
        try:
            result = memcache.get(key_)
        except Exception:
            result = None
        if nocache or result is None:
            result = cls.get(primary_key)
            memcache.set(key=key_, value=result)
        return result

    @classmethod
    def get_cached_list(cls, query_key,params=[],nocache=False):
        """Return the cached list with the specified key.
        User must keep the key unique, and the query must
        be same instance of the class .
        """
        key_ = cls.__name__ +"_list_" + query_key
        try:
            result = memcache.get(key_)
        except Exception:
            result = None
        if nocache or result is None:
            if query_key in cls.querys:
                params_ = [cls.querys[query_key]] + params
                query = db.GqlQuery(*params_ )
                result = query.fetch(1000)
                memcache.add(key=key_, value=result)
            else:
                raise Exception("Query for object list does not define in the Class Model.")
        return result

    @classmethod
    def get_cached_page(cls, query_key,page,num_per_page,count=None,params=[],nocache=False):
        """Return the cached list with the specified key and page.
        for example we need to query the user's checklist page,
        then we set: query_ley = "user_checklist"+user.user_id()

        the params is used for inject to gql.
        """
        key_ = cls.__name__ +"_page_" + query_key
        if params is not None:
            key_ = key_ + "_" + "_".join(str(param) for param in params)
        try:
            obj_pages = memcache.get(key_)
        except Exception:
            obj_pages = None
        if obj_pages is None or page not in obj_pages:
            try:
                if query_key in cls.page_querys:
                    params_ = [cls.page_querys[query_key]] + params
                    query = db.GqlQuery(*params_ )
                    obj_page = GqlQueryPaginator(query,page,num_per_page,count).page()
                    if obj_pages is None:
                        obj_pages = {}
                    obj_pages[page] = obj_page
                    memcache.set(key=key_, value=obj_pages)
                else:
                    raise Exception("Query for object page does not define in the Class %s.", cls.__name__)
            except InvalidPage:
                return None
        return obj_pages[page]


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
