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
        for qry in (_raidgroup, _sar):
            await connection.execute(qry)
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
    "id" numeric,
    "date" timestamp,
    "gid" numeric,
    "export_data" json default '{}'::json,
    "level" text
);"""

_sar = """CREATE TABLE IF NOT EXISTS Sar(
    "id" numeric PRIMARY KEY,
    "group1_name" text,
    "group1_roles" text,
    "group1_excl" bool,
    "group2_name" text,
    "group2_roles" text,
    "group2_excl" bool,
    "group3_name" text,
    "group3_roles" text,
    "group3_excl" bool,
    "group4_name" text,
    "group4_roles" text,
    "group4_excl" bool,
    "group5_name" text,
    "group5_roles" text,
    "group5_excl" bool
)"""

_migrators = (
    """ALTER TABLE RaidGroup ADD COLUMN IF NOT EXISTS "level" text;""",
    """ALTER TABLE RaidGroup ADD COLUMN IF NOT EXISTS "date" timestamp;""",
)

RaidGroup = defaultdict(lambda: dict(id=0, date="", gid=0, export_data={}, level=""))
