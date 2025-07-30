# pylint: disable=unused-import, unused-argument, redefined-outer-name, protected-access
import os

import pytest

import snowflake.connector as sc


@pytest.fixture(scope="module")
def fixture_snowflake_credentials():
    """Mocked Snowflake Credentials. Ignored if environment variables have been set."""
    if not os.environ.get("SNOWFLAKE_ACCOUNT"):
        os.environ["SNOWFLAKE_ACCOUNT"] = "test_account"
        os.environ["SNOWFLAKE_PASSWORD"] = "test_password"
        os.environ["SNOWFLAKE_USERNAME"] = "test_username"
    yield


@pytest.fixture(scope="module")
def fixture_snowflake_credentials_private_link():
    """Mocked Snowflake Credentials. Ignored if environment variables have been set."""
    os.environ["SNOWFLAKE_ACCOUNT"] = "test_account.privatelink"
    os.environ["SNOWFLAKE_PASSWORD"] = "test_password"
    os.environ["SNOWFLAKE_USERNAME"] = "test_username"


@pytest.fixture(scope="module")
def fixture_snowflake_credentials_ssm():
    """Mocked Snowflake SSM Credentials. Ignored if environment variables have been set."""
    if not os.environ.get("SNOWFLAKE_ACCOUNT"):
        os.environ["SNOWFLAKE_ACCOUNT"] = "boto+ssm:test/snowflake/account"
        os.environ["SNOWFLAKE_PASSWORD"] = "boto+ssm:test/snowflake/password"
        os.environ["SNOWFLAKE_USERNAME"] = "boto+ssm:test/snowflake/username"
    yield


@pytest.fixture(scope="function")
def fixture_snowflake_connector(monkeypatch):
    """Monkeypatched Snowflake connector methods. Ignored if actual SNOWFLAKE_ACCOUNT is being used."""

    def mock_connect(account=None, user=None, password=None, role=None, warehouse=None):
        return sc.SnowflakeConnection(
            account=account,
            password=password,
            role=role,
            user=user,
            warehouse=warehouse,
        )

    def mock_init(self, account, password, role, user, warehouse):
        self._account = account
        self._password = password
        self._role = role
        self._user = user
        self._warehouse = warehouse

    def mock_close(*args, **kwargs):
        return "Closed"

    def mock_cursor(*args, **kwargs):
        return sc.DictCursor(connection=kwargs.get("conn"))

    if "test" in os.environ["SNOWFLAKE_ACCOUNT"]:
        monkeypatch.setattr(sc.SnowflakeConnection, "__init__", mock_init)
        monkeypatch.setattr(sc.SnowflakeConnection, "close", mock_close)
        monkeypatch.setattr(sc.SnowflakeConnection, "cursor", mock_cursor)
        monkeypatch.setattr(sc, "connect", mock_connect)
    yield


@pytest.fixture(scope="function")
def fixture_snowflake_cursor(monkeypatch):
    """Monkeypatched Snowflake connector methods. Ignored if actual SNOWFLAKE_ACCOUNT is being used."""

    def mock_init(self, connection):
        self._connection = connection

    def mock_close(*args, **kwargs):
        return "Closed"

    def mock_execute(self, *args, **kwargs):
        self.query = kwargs.get("query")
        self._result = [{"1": 1}]
        return self

    def mock_fetchall(self, *args, **kwargs):
        return self._result

    if "test" in os.environ["SNOWFLAKE_ACCOUNT"]:
        monkeypatch.setattr(sc.DictCursor, "__init__", mock_init)
        monkeypatch.setattr(sc.DictCursor, "close", mock_close)
        monkeypatch.setattr(sc.DictCursor, "execute", mock_execute)
        monkeypatch.setattr(sc.DictCursor, "fetchall", mock_fetchall)
    yield
