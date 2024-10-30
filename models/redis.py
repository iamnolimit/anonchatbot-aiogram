import redis
import hashlib

# Redis connection configuration
REDIS_CONFIG = {
    'host': 'redis-16032.c100.us-east-1-4.ec2.redns.redis-cloud.com',
    'port': 16032,  # Port should be an integer, not string
    'username': 'default',
    'password': 'Rn9flXWi5hd4Yd90wXQGGfUXcHzTVPSw',
    'decode_responses': True  # Automatically decode bytes to strings
}

def get_redis_connection():
    return redis.Redis(**REDIS_CONFIG)

def add_in_queue(user_id):
    with get_redis_connection() as r:
        # Convert user_id to string before storing
        r.rpush('search_queue', str(user_id))

def del_from_queue(user):
    with get_redis_connection() as r:
        # Convert user to string before removing
        r.lrem("search_queue", 0, str(user))

def get_interlocutor(user):
    with get_redis_connection() as r:
        if r.llen("search_queue") >= 2:
            # Remove the current user from queue first
            r.lrem("search_queue", 0, str(user))
            # Get the next user from queue
            value = r.lpop("search_queue")
            try:
                return int(value) if value else False
            except (ValueError, TypeError):
                return False
        return False

def check_queue():
    with get_redis_connection() as r:
        return r.llen("search_queue") >= 2

def create_dialogue(user_1, user_2):
    with get_redis_connection() as r:
        # Convert both users to strings before storing
        r.hset("dialogues", str(user_1), str(user_2))
        r.hset("dialogues", str(user_2), str(user_1))

def del_dialogue(user1, user2):
    with get_redis_connection() as r:
        # Convert users to strings before deleting
        r.hdel("dialogues", str(user1))
        r.hdel("dialogues", str(user2))

def find_dialogue(id):
    with get_redis_connection() as r:
        # Convert id to string for lookup
        value = r.hget("dialogues", str(id))
        try:
            return int(value) if value else None
        except (ValueError, TypeError):
            return None

def check(user) -> bool:
    with get_redis_connection() as r:
        # Convert user to string for lookup
        return bool(r.hget("states", str(user)))
