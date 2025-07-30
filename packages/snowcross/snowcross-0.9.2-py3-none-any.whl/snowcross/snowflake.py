import contextlib
import logging
import os
import subprocess
from pathlib import Path
from typing import Iterator, Optional
from uuid import uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

import snowflake.connector as sc
from snowflake.snowpark.session import Session

from .errors import ResourceLockedError

MAX_LOCK_RETRIES = 2


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def connection(
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_passphrase: Optional[str] = None,
    allow_privatelink: bool = True,
    **kwargs,
) -> Iterator[sc.SnowflakeConnection]:
    """Establish connection to Snowflake.

    Args:
        password (Optional[str], optional): Password (do not specify with private key). Defaults to None.
        private_key (Optional[str], optional): Private key payload (do not specify with password). Defaults to None.
        private_key_path (Optional[str], optional): Path to private key file (do not specify with password). Defaults to None.
        private_key_passphrase (Optional[str], optional): Passcode to decrypt private key file, if encrypted (do not specify with password). Defaults to None.
        allow_privatelink (bool): PrivateLink enabled. Defaults to True.

    Yields:
        Iterator[sc.SnowflakeConnection]: Snowflake connection context.
    """
    conn_args = connection_args(
        password=password,
        private_key=private_key,
        private_key_path=private_key_path,
        private_key_passphrase=private_key_passphrase,
        allow_privatelink=allow_privatelink,
        **kwargs,
    )

    sc.paramstyle = "format"

    conn = None
    try:
        conn = sc.connect(**conn_args)
        yield conn
    finally:
        if conn:
            conn.close()


@contextlib.contextmanager
def snowpark_connection(
    password: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_passphrase: Optional[str] = None,
    allow_privatelink: bool = True,
    **kwargs,
) -> Iterator[Session]:
    """Establish a Snowpark connection to Snowflake.

    Args:
        password (Optional[str], optional): Password (do not specify with private key). Defaults to None.
        private_key (Optional[str], optional): Private key payload (do not specify with password). Defaults to None.
        private_key_path (Optional[str], optional): Path to private key file (do not specify with password). Defaults to None.
        private_key_passphrase (Optional[str], optional): Passcode to decrypt private key file, if encrypted (do not specify with password). Defaults to None.
        allow_privatelink (bool): PrivateLink enabled. Defaults to True.

    Yields:
        Iterator[Session]: Snowpark connection context.
    """
    conn_args = connection_args(
        password=password,
        private_key_path=private_key_path,
        private_key_passphrase=private_key_passphrase,
        allow_privatelink=allow_privatelink,
        **kwargs,
    )

    conn = None
    try:
        conn = Session.builder.configs(conn_args).create()
        yield conn
    finally:
        if conn:
            conn.close()


def connection_args(
    password: Optional[str] = None,
    private_key: Optional[str] = None,
    private_key_path: Optional[str] = None,
    private_key_passphrase: Optional[str] = None,
    allow_privatelink: bool = True,
    **kwargs,
) -> dict:
    """Builds Snowflake connection arguments.

    Args:
        password (Optional[str], optional): Password (do not specify with private key). Defaults to None.
        private_key (Optional[str], optional): Private key payload (do not specify with password). Defaults to None.
        private_key_path (Optional[str], optional): Path to private key file (do not specify with password). Defaults to None.
        private_key_passphrase (Optional[str], optional): Passcode to decrypt private key file, if encrypted (do not specify with password). Defaults to None.
        allow_privatelink (bool): PrivateLink enabled. Defaults to True.

    Returns:
        dict: Dictionary of all connection arguments with authentication ones resolved.
    """

    res = {**kwargs}

    if password:
        res["password"] = password
    elif private_key:
        private_key_lines = private_key.strip().split("\n")
        if (
            len(private_key_lines) > 1
            and private_key_lines[0] == "-----BEGIN PRIVATE KEY-----"
            and private_key_lines[-1] == "-----END PRIVATE KEY-----"
        ):
            private_key = "".join(private_key_lines[1:-1])

        res["private_key"] = private_key
    elif private_key_path:
        with open(os.path.expanduser(private_key_path), "rb") as key:
            res["private_key"] = serialization.load_pem_private_key(
                data=key.read(),
                password=private_key_passphrase.encode() if private_key_passphrase else None,
                backend=default_backend(),
            ).private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

    if not allow_privatelink:
        res["account"] = res["account"].replace(".privatelink", "")

    return res


@contextlib.contextmanager
def cursor(conn: sc.SnowflakeConnection) -> Iterator[sc.cursor.SnowflakeCursor]:
    """Initialize Snowflake dict cursor.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.

    Yields:
        Snowflake dictionary cursor generator.
    """
    dict_cursor = None
    try:
        dict_cursor = conn.cursor(sc.cursor.DictCursor)
        yield dict_cursor
    finally:
        if dict_cursor:
            dict_cursor.close()


def execute_statement(conn: sc.SnowflakeConnection, sql: str, **kwargs):
    """Pass statement to Snowflake to execute.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.
        sql (str): The Snowflake SQL statement to execute.
    """
    with cursor(conn) as cur:
        cur.execute(sql, **kwargs)


def execute_query(conn: sc.SnowflakeConnection, sql: str, **kwargs) -> Optional[list]:
    """Pass SQL to Snowflake and return the result as a dictionary.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.
        sql: The Snowflake SQL to execute.
    Returns:
        A list of dictionaries representing the results of the query, or None if some error happened.
    """
    with cursor(conn) as cur:
        res = cur.execute(sql, **kwargs)
        if not res:
            return None
        return res.fetchall()


@contextlib.contextmanager
def lock(
    client: str,
    resource: str,
    conn: sc.SnowflakeConnection,
    table: str = "lock",
    session_lock: bool = False,
) -> Iterator[str]:
    """Creates a lock using a Snowflake table.

    Args:
        client (str): The client requesting the lock.
        resource (str): The resource to lock.
        conn (SnowflakeConnection): The Snowflake connection to use.
        table (str, optional): The table to use for locking, it will be created if it does not exist. Defaults to "lock".
        session_lock (bool, optional): Whether to prevent different sessions of the same client acquiring the lock. Defaults to False.

    Yields:
        Iterator[str]: The session id of the lock.
    """
    session_id = str(uuid4())
    lock_acquired = False
    retry_attempt = 0

    while retry_attempt < MAX_LOCK_RETRIES:
        try:
            logger.info("Attempting to acquire lock on %s for %s", resource, client)
            execute_statement(
                conn=conn,
                sql=f"""
                    merge into {table} using (
                        select
                        '{client}' as client,
                        '{resource}' as resource,
                        '{session_id}' as session_id,
                        {session_lock} as session_locked
                    ) as s on s.resource = lock.resource
                    when not matched then insert (client, resource, acquired, session_id, session_locked) values (s.client, s.resource, true, s.session_id, s.session_locked)
                    when matched and lock.acquired=false or (lock.client = s.client and s.session_locked = false) then update set
                        lock.client=s.client,
                        lock.acquired=true,
                        lock.session_id=s.session_id,
                        lock.session_locked=s.session_locked;
                """,
            )

            row = execute_query(
                conn=conn,
                sql=f"""
                    select 
                        client,
                        session_id
                    from {table}
                    where resource='{resource}'
                """,
            )

            if row:
                in_use_client = row[0].get("CLIENT")
                if in_use_client != client:
                    raise ResourceLockedError(
                        f"{resource} is in use by {in_use_client}, could not acquire lock for {client}"
                    )

                if session_lock and row[0].get("SESSION_ID") != session_id:
                    raise ResourceLockedError(
                        f"{resource} is in use by another session of {client}, could not acquire lock"
                    )

            lock_acquired = True
            yield session_id
        except sc.errors.ProgrammingError as e:
            table_not_exists = f"Object '{table.upper()}' does not exist or not authorized."
            if not e.msg or not table_not_exists in e.msg:
                raise e

            logger.warning(e.msg)
            execute_statement(
                conn=conn,
                sql=f"""
                    create table {table} if not exists (
                        client varchar,
                        resource varchar,
                        acquired boolean,
                        session_id varchar,
                        session_locked boolean,
                        primary key(client,resource)
                    )
                    data_retention_time_in_days=0
                    change_tracking=false
                """,
            )
            logger.info("Created lock table %s and retrying", table)
        finally:
            if lock_acquired:
                logger.info("Releasing lock for %s", resource)
                execute_query(
                    conn=conn,
                    sql=f"""
                    update {table}
                    set acquired=false
                    where resource='{resource}'
                    """,
                )
                retry_attempt = MAX_LOCK_RETRIES


def generate_key(name: str, target_dir: Optional[str] = None):
    """Generates private and public key files.

    Args:
        name (str): Name of the key.
        target_dir (str, optional): Target key target_directory. Defaults to ~/.ssh.
    """

    path = Path(os.path.expanduser(target_dir if target_dir else str(Path.home() / ".ssh")))
    prv_path = path / f"{name}.p8"
    pub_path = path / f"{name}.pub"

    if prv_path.is_file() != pub_path.is_file():
        raise ValueError(
            f"Found private OR public key only for {name} in {target_dir}, delete to re-generate"
        )

    os.makedirs(path, exist_ok=True)

    if not prv_path.is_file() and not pub_path.is_file():
        # Step 1: Generate the Private Key
        # https://docs.snowflake.com/en/user-guide/key-pair-auth.html#step-1-generate-the-private-key
        retcode = _shell(
            f'openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out "{prv_path}" -nocrypt'
        )
        if retcode != 0:
            raise ValueError(f"Return code {retcode} received from openssl")

        # Step 2: Generate a Public Key
        # https://docs.snowflake.com/en/user-guide/key-pair-auth.html#step-2-generate-a-public-key
        retcode = _shell(f'openssl rsa -in "{prv_path}" -pubout -out "{pub_path}"')
        if retcode != 0:
            raise ValueError(f"Return code {retcode} received from openssl")


def _shell(command: str) -> int:
    p = subprocess.Popen(command, shell=True)
    p.communicate()
    return p.returncode
