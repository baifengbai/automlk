import os
import json
import time
import logging
from .config import get_use_redis, set_use_redis
from .context import get_config, get_data_folder

log = logging.getLogger(__name__)

# try to import redis
__config = get_config()
if __config['store'] == 'redis':
    try:
        import redis
        rds = redis.Redis(host=__config['store_url'])
        print('using redis')
        set_use_redis(True)
    except:
        set_use_redis(False)
        log.error('redis not installed: using file storage instead')

if not get_use_redis():
    # we will use simple file storage
    store_folder = get_data_folder() + '/store'
    if not store_folder:
        os.makedirs(store_folder)


def get_key_store(key):
    """
    retieves value from key in store

    :param key: key of the data
    :return: value of the data
    """
    if get_use_redis():
        return json.loads(rds.get(str(key)))
    else:
        try:
            if exists_key_store(key):
                return json.load(open(store_folder + '/' + __clean_key(key) + '.json', 'r'))
            else:
                return None
        except:
            return None


def set_key_store(key, value):
    """
    sets value to key in store

    :param key: key of the data
    :param value: value of the data to store
    """
    if get_use_redis():
        rds.set(str(key), json.dumps(value))
    else:
        with open(store_folder + '/' + __clean_key(key) + '.json', 'w') as f:
            json.dump(value, f)


def exists_key_store(key):
    """
    checks if a key exists

    :param key: key of the data
    :return: True if the key exists else False
    """
    if get_use_redis():
        return rds.exists(str(key))
    else:
        return os.path.exists(store_folder + '/' + __clean_key(key) + '.json')


def del_key_store(key):
    """
    deletes key in store

    :param key: key of the data
    :return: None
    """
    if get_use_redis():
        rds.delete(str(key))
    else:
        if exists_key_store(key):
            os.remove(store_folder + '/' + __clean_key(key) + '.json')


def incr_key_store(key, amount=1):
    """
    increments value of key in store with amount

    :param key: key of the data
    :param amount: amount to add
    :return: new value
    """
    if get_use_redis():
        return rds.incr(str(key), amount)
    else:
        if exists_key_store(key):
            value = get_key_store(key)
            set_key_store(key, value + amount)
            return value + amount
        else:
            set_key_store(key, amount)
            return amount


def get_counter_store(key):
    """
    returns raw value of key in store with amount

    :param key: key of the data
    :return: counter
    """
    if get_use_redis():
        if rds.exists(str(key)):
            return int(rds.get(str(key)))
        else:
            return 0
    else:
        if exists_key_store(key):
            return get_key_store(key)
        else:
            return 0


def rpush_key_store(key, value):
    """
    add value to the end of a list of key in store

    :param key: key of the data
    :return: value of the data
    :return: None
    """
    if get_use_redis():
        rds.rpush(str(key), json.dumps(value))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if isinstance(l, list):
                set_key_store(key, l + [value])
            else:
                set_key_store(key, [value])
        else:
            set_key_store(key, [value])


def rpop_key_store(key):
    """
    returns and pop the 1st element of a list of key in store

    :param key: key of the data
    :return: value
    """
    if get_use_redis():
        return json.loads(rds.rpop(str(key)))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if isinstance(l, list):
                e = l[0]
                set_key_store(key, l[1:])
                return e
            else:
                set_key_store(key, [])
                return []
        else:
            return None


def lrem_key_store(key, value):
    """
    removes value from the list of key in store

    :param key: key of the data
    :return: value of the data
    :return: None
    """
    if get_use_redis():
        rds.lrem(str(key), json.dumps(value))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            lr = [x for x in l if x != value]
            set_key_store(key, lr)


def brpop_key_store(key):
    """
    returns and pop the 1st element of a list of key in store with blocking

    :param key: key of the data
    :return: value
    """
    if get_use_redis():
        return json.loads(rds.brpop(str(key))[1])
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if isinstance(l, list) and len(l) > 0:
                e = l[0]
                if len(l) > 1:
                    set_key_store(key, l[1:])
                else:
                    set_key_store(key, [])
                return e
            else:
                time.sleep(1)
                return None
        else:
            time.sleep(1)
            return None


def lpush_key_store(key, value):
    """
    add value to the beginning of a list of key in store

    :param key: key of the data
    :return: value of the data
    :return: None
    """
    if get_use_redis():
        rds.lpush(str(key), json.dumps(value))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if isinstance(l, list):
                set_key_store(key, [value] + l)
            else:
                set_key_store(key, [value])
        else:
            set_key_store(key, [value])


def list_key_store(key):
    """
    returns the complete list of values

    :param key: key of the data
    :return: list
    """
    if get_use_redis():
        return [json.loads(x) for x in rds.lrange(key, 0, -1)]
    else:
        l = get_key_store(key)
        if l != None:
            return l
        else:
            return []


def llen_key_store(key):
    """
    returns the length of a list of key in store

    :param key: key of the data
    :return: length
    """
    if get_use_redis():
        return rds.llen(str(key))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if isinstance(l, list):
                return len(l)
            else:
                return 0
        else:
            return 0


def sadd_key_store(key, value):
    """
    add value to set key

    :param key: key of the data
    :return: value of the data
    :return: None
    """
    if get_use_redis():
        return rds.sadd(str(key), json.dumps(value))
    else:
        if exists_key_store(key):
            l = get_key_store(key)
            if value not in l:
                set_key_store(key, [value] + l)
        else:
            set_key_store(key, [value])


def smembers_key_store(key):
    """
    returns members of set key

    :param key: key of the data
    :return: list
    """
    if get_use_redis():
        return [json.loads(m) for m in rds.smembers(str(key))]
    else:
        return get_key_store(key)


def __clean_key(key):
    """
    modify name of the key in order to be usable in file store

    :param key: key of the data
    :return: key with : replaces by __
    """
    return str(key).replace(':', '__')
