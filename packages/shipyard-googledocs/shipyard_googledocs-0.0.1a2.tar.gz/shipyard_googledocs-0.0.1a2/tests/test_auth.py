import os
import pytest
from shipyard_googledocs import GoogleDocsClient
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
env_exists = dotenv_path != ""
if env_exists:
    load_dotenv(dotenv_path)


@pytest.fixture
def valid_credentials():
    return os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


@pytest.mark.skipif(not env_exists, reason="No .env file found")
def test_good_connection(valid_credentials):
    client = GoogleDocsClient(valid_credentials)
    assert (
        client.connect() == 0
    ), "Expected successful connection (0), but got different result."


@pytest.mark.skipif(not env_exists, reason="No .env file found")
def test_bad_connection(monkeypatch):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "{creds:bad_credentials}")

    client = GoogleDocsClient("bad_credentials")
    assert (
        client.connect() == 1
    ), "Expected failed connection (1), but got different result."
