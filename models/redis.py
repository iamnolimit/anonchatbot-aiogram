import redis
import hashlib

# Redis connection configuration
REDIS_CONFIG = {
    'host': 'redis-16032.c100.us-east-1-4.ec2.redns.redis-cloud.com',
    'port': 16032,
    'db': 'cache-M2WCFBEM',
    'username': 'default',
    'password': 'Rn9flXWi5hd4Yd90wXQGGfUXcHzTVPSw',
}

def get_redis_connection():
    return redis.Redis(**REDIS_CONFIG)

def add_in_queue(user_id):
    with get_redis_connection() as r:
        r.rpush('search_queue', user_id)

def del_from_queue(user):
    with get_redis_connection() as r:
        r.lrem("search_queue", 0, user)

def get_interlocutor(user):
    with get_redis_connection() as r:
        if r.llen("search_queue") >= 2:
            r.lrem("search_queue", 0, user)
            value = r.lpop("search_queue")
            return int(value) if value else False
        return False

def check_queue():
    with get_redis_connection() as r:
        return r.llen("search_queue") >= 2

def create_dialogue(user_1, user_2):
    with get_redis_connection() as r:
        r.hset("dialogues", user_1, user_2)
        r.hset("dialogues", user_2, user_1)

def del_dialogue(user1, user2):
    with get_redis_connection() as r:
        r.hdel("dialogues", user1)
        r.hdel("dialogues", user2)

def find_dialogue(id):
    with get_redis_connection() as r:
        value = r.hget("dialogues", id)
        return int(value) if value else None

def check(user) -> bool:
    with get_redis_connection() as r:
        return bool(r.hget("states", user))
