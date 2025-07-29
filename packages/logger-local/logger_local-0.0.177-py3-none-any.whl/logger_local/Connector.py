from functools import lru_cache

import mysql.connector
from python_sdk_remote.utilities import get_sql_hostname, get_sql_username, get_sql_password, our_get_env


# We are using the database directly to avoid cyclic dependency
@lru_cache
def get_connection(schema_name: str, is_treading: bool = False) -> mysql.connector:
    # is_treading is used to get a dedicated connection from cache.
    if schema_name == "logger":
        host = our_get_env(key="LOGGER_MYSQL_HOSTNAME", default=get_sql_hostname())
        user = our_get_env(key="LOGGER_MYSQL_USERNAME", default=get_sql_username())
        password = our_get_env(key="LOGGER_MYSQL_PASSWORD", default=get_sql_password())

    else:
        host = get_sql_hostname()
        user = get_sql_username()
        password = get_sql_password()

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=schema_name
        )
    except Exception as e:
        raise Exception(f"Error connecting to MySQL: {e}. {host=}, {password=}, {user=}, {schema_name=}")
    return connection
