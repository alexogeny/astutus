import os
import asyncpg
import json
from datetime import datetime
from collections import defaultdict


async def init_connection(conn):
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


async def get_db():
    path = os.environ.get("DATABASE_URL", "postgres://postgres:root@localhost/postgres")
    pool = await asyncpg.create_pool(
        dsn=path, command_timeout=60, max_size=5, min_size=1, init=init_connection
    )
    async with pool.acquire() as connection:
        await connection.execute(_raidgroup)
        for migrator in _migrators:
            await connection.execute(migrator)
    return pool


_base = """
CREATE TABLE IF NOT EXISTS "{name}"(
    id numeric PRIMARY KEY,
    "create" timestamp,
    "update" timestamp,
    {fields}
);
"""

_raidgroup = """CREATE TABLE IF NOT EXISTS RaidGroup(
    "id" numeric PRIMARY KEY,
    "gid" numeric,
    "export_data" jsonb default '{}'::jsonb,
    "level" text
);"""

_migrators = ("""ALTER TABLE RaidGroup ADD COLUMN IF NOT EXISTS "level" text;""",)

RaidGroup = defaultdict(lambda: dict(id=0, gid=0, export_data={}, level=""))
