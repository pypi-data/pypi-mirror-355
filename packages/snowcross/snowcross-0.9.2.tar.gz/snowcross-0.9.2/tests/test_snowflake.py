"""Snowflake testing suite. Can be run against live Snowflake environment if SNOWFLAKE_ACCOUNT and AUTH environment variables are defined."""

# pylint: disable=unused-import, unused-argument, redefined-outer-name, protected-access
import os

import snowflake.connector as sc
from snowcross.snowflake import (
    connection,
    connection_args,
    cursor,
    execute_query,
    execute_statement,
)
from tests.fixtures.aws import (
    aws_credentials,
    fixture_ssm_client,
    fixture_ssm_params_snowflake,
)
from tests.fixtures.snowflake import (
    fixture_snowflake_connector,
    fixture_snowflake_credentials,
    fixture_snowflake_credentials_private_link,
    fixture_snowflake_credentials_ssm,
    fixture_snowflake_cursor,
)


def test_connection_args():
    test_password = "test_password"
    conn_args = connection_args(password=test_password)
    assert conn_args["password"] == test_password


def test_connection_args_privatelink():
    conn_args = connection_args(account="abc123.privatelink", allow_privatelink=False)
    assert conn_args["account"] == "abc123"

    account = "abc123"
    conn_args = connection_args(account=account, allow_privatelink=False)
    assert conn_args["account"] == account
    conn_args = connection_args(account=account, allow_privatelink=True)
    assert conn_args["account"] == account


def test_connection(monkeypatch, fixture_snowflake_credentials, fixture_snowflake_connector):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
        private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
    ) as conn:
        assert type(conn) == sc.SnowflakeConnection


def test_connection_account_not_allow_privatelink(
    monkeypatch, fixture_snowflake_credentials_private_link, fixture_snowflake_connector
):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        allow_privatelink=False,
    ) as conn:
        assert ".privatelink" not in conn.account


def test_connection_account_allow_privatelink(
    monkeypatch, fixture_snowflake_credentials_private_link, fixture_snowflake_connector
):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
    ) as conn:
        assert ".privatelink" in conn.account


def test_cursor(
    monkeypatch,
    fixture_snowflake_credentials,
    fixture_snowflake_connector,
    fixture_snowflake_cursor,
):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
        private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
    ) as conn:
        with cursor(conn) as cur:
            assert type(cur) == sc.DictCursor


def test_execute_statement(
    monkeypatch,
    fixture_snowflake_credentials,
    fixture_snowflake_connector,
    fixture_snowflake_cursor,
):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
        private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
    ) as conn:
        execute_statement(conn=conn, sql="select 1;")


def test_execute_query(
    monkeypatch,
    fixture_snowflake_credentials,
    fixture_snowflake_connector,
    fixture_snowflake_cursor,
):
    with connection(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USERNAME"],
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
        private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
    ) as conn:
        res = execute_query(conn=conn, sql="select 1;")

    assert len(res) == 1
    assert res[0]["1"] == 1
