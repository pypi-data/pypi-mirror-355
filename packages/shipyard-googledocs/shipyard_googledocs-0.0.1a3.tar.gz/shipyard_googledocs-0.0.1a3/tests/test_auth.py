from unittest.mock import patch, Mock, PropertyMock
from shipyard_googledocs import GoogleDocsClient


class TestAuthConnect:
    def test_connect_failure_with_bad_creds(self):
        with (
            patch("shipyard_googledocs.googledocs.build", return_value=Mock()),
            patch.object(
                GoogleDocsClient,  # target class
                "credentials",  # property name
                new_callable=PropertyMock,  # because it's @property
                side_effect=Exception("bad creds"),
            ),
        ):
            client = GoogleDocsClient(service_account_credential="ignored")
            assert client.connect() == 1, "bad creds should return 1"

    def test_connect_success_with_valid_creds(self):
        fake_creds = Mock(name="fake_creds")
        fake_service = Mock(name="fake_service")

        with (
            patch("shipyard_googledocs.googledocs.build", return_value=fake_service),
            patch.object(
                GoogleDocsClient,
                "credentials",
                new_callable=PropertyMock,
                return_value=fake_creds,
            ),
        ):
            client = GoogleDocsClient(service_account_credential="ignored")
            assert client.connect() == 0, "valid creds should return 0"
