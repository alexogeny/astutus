import asyncio
import aioredis as redis


class Redis:
    def __init__(self):
        self.connection_pool = None

    async def connect_pool(self, host, port, pw=None):
        if self.connection_pool is not None and not self.connection_pool.closed:
            return
        self.connection_pool = await redis.create_redis_pool(
            (host, port), password=pw, maxsize=10
        )

    async def reconnect(self):
        self.connection_pool = await redis.create_redis_pool(
            self.connection_pool.address
        )

    def disconnect(self):
        if self.connection_pool is None:
            return
        self.connection_pool.close()

    async def get(self, key, default=None):
        if default is not None:
            if not await self.exists(key):
                return default
        return await self.execute("GET", key)

    async def increment(self, key):
        return await self.execute("INCR", key)

    async def zincrement(self, key, member):
        return await self.execute("ZINCRBY", key, 1, member)

    async def zscore(self, key, member):
        return await self.execute("ZSCORE", key, member)

    async def zadd(self, key, member, value):
        return await self.execute("ZADD", key, value, member)

    async def zrem(self, key, member):
        return await self.execute("ZREM", key, member)

    async def zrank(self, key, member):
        return await self.execute("ZREVRANK", key, member)

    async def zbyscore(self, key, min, max):
        return await self.execute("ZRANGEBYSCORE", key, min, max)

    async def zrembyscore(self, key, min, max):
        return await self.execute("ZREMRANGEBYSCORE", key, min, max)

    async def rpush(self, key, *values):
        return await self.execute("RPUSH", key, *values)

    async def lpop(self, key):
        return await self.execute("LPOP", key)

    async def llen(self, key):
        return await self.execute("LLEN", key)

    async def lrange(self, key, start, end):
        return await self.execute("LRANGE", key, start, end)

    async def set(self, key, value, *args):
        return await self.execute("SET", key, value, *args)

    async def sadd(self, key, *values):
        return await self.execute("SADD", key, *values)

    async def srem(self, key, *values):
        return await self.execute("SREM", key, *values)

    async def smembers(self, key):
        return await self.execute("SMEMBERS", key)

    async def hset(self, key, member, value):
        return await self.execute("HSET", key, member, value)

    async def hget(self, key, member):
        return await self.execute("HGET", key, member)

    async def hgetall(self, key):
        return await self.execute("HGETALL", key)

    async def exists(self, *values):
        return await self.execute("EXISTS", *values) == len(values)

    async def size(self):
        return await self.execute("DBSIZE")

    async def execute(self, command, *args):
        if self.connection_pool is None or self.connection_pool.closed:
            try:
                await self.reconnect()
            except:
                return
        with await self.connection_pool as connection:
            value = await connection.execute(command, *args)
        return await self.decode_value(value)

    async def decode_value(self, value):
        if type(value) == list:
            return [await self.decode_value(v) for v in value]
        elif type(value) == bytes:
            return value.decode()

        return value
