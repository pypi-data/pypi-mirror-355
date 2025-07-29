import random
import string
from collections.abc import Generator
from contextlib import contextmanager

import pyexasol  # type: ignore
from tenacity import retry
from tenacity.stop import stop_after_attempt


@retry(reraise=True, stop=stop_after_attempt(3))
def _create_random_schema(conn: pyexasol.ExaConnection, schema_name_length: int) -> str:
    """
    The function creates a schema with randomly generated name. It makes a few retries,
    as it's theoretically possible to create a collision with an existing schema.
    """

    schema = "".join(random.choice(string.ascii_letters) for _ in range(schema_name_length))
    sql = f'CREATE SCHEMA "{schema}";'
    conn.execute(query=sql)
    return schema


def get_schema(conn: pyexasol.ExaConnection) -> str | None:
    return conn.execute(f"SELECT CURRENT_SCHEMA;").fetchval()


def set_schema(conn: pyexasol.ExaConnection, schema: str | None):
    if schema:
        conn.execute(f'OPEN SCHEMA "{schema}";')
    else:
        conn.execute("CLOSE SCHEMA;")


def delete_schema(conn: pyexasol.ExaConnection, schema: str) -> None:
    sql = f'DROP SCHEMA IF EXISTS "{schema}" CASCADE;'
    conn.execute(query=sql)


@contextmanager
def temp_schema(
    conn: pyexasol.ExaConnection, schema_name_length: int = 20
) -> Generator[str, None, None]:
    """
    A context manager for running an operation in a newly created temporary schema.
    The schema will be deleted after the operation is competed. Note, that all objects
    created in this schema will be deleted with it. Returns the name of the created schema.

    conn                - pyexasol connection.
    schema_name_length  - Number of characters in the temporary schema name.
    """
    current_schema = get_schema(conn)
    schema = ""
    try:
        schema = _create_random_schema(conn, schema_name_length)
        yield schema
    finally:
        delete_schema(conn, schema)
        set_schema(conn, current_schema)
