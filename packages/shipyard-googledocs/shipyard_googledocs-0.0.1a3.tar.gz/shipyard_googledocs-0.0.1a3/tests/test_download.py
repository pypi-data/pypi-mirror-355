import unittest
from unittest.mock import patch, Mock, PropertyMock
from shipyard_googledocs.googledocs import GoogleDocsClient
from shipyard_googledocs import exceptions


class TestGoogleDocsClient(unittest.TestCase):

    def setUp(self):
        self.credentials_patch = patch.object(
            GoogleDocsClient, "credentials", new_callable=PropertyMock
        )
        self.mock_credentials = self.credentials_patch.start()
        self.mock_credentials.return_value = "mocked_creds"

        self.build_patch = patch("shipyard_googledocs.googledocs.build")
        self.mock_build = self.build_patch.start()

        self.mock_doc_service = Mock()
        self.mock_build.return_value = self.mock_doc_service

        self.client = GoogleDocsClient(service_account_credential="fake")

        self.doc_id = "123docID"
        self.extract_patch = patch.object(
            GoogleDocsClient, "extract_doc_id_from_url", return_value=self.doc_id
        )
        self.extract_patch.start()

    def tearDown(self):
        patch.stopall()

    def test_successful_fetch(self):
        self.mock_doc_service.documents.return_value.get.return_value.execute.return_value = {
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [{"textRun": {"content": "Test paragraph"}}]
                        }
                    }
                ]
            }
        }

        result = self.client.fetch(
            f"https://docs.google.com/document/d/{self.doc_id}/edit"
        )
        self.assertIn("Test paragraph", result)

    def test_invalid_url_raises(self):
        with patch.object(
            GoogleDocsClient, "extract_doc_id_from_url", return_value=None
        ):
            with self.assertRaises(exceptions.InvalidDocUrlError):
                self.client.fetch("not_a_valid_doc_url")

    def test_empty_doc_raises(self):
        self.mock_doc_service.documents.return_value.get.return_value.execute.return_value = {
            "body": {"content": []}
        }

        with self.assertRaises(exceptions.DownloadError) as ctx:
            self.client.fetch(f"https://docs.google.com/document/d/{self.doc_id}/edit")

        self.assertIn("empty", str(ctx.exception))

    def test_api_failure_raises(self):
        self.mock_doc_service.documents.return_value.get.return_value.execute.side_effect = Exception(
            "Google API down"
        )

        with self.assertRaises(exceptions.DownloadError) as ctx:
            self.client.fetch(f"https://docs.google.com/document/d/{self.doc_id}/edit")

        self.assertIn("Google API down", str(ctx.exception))
