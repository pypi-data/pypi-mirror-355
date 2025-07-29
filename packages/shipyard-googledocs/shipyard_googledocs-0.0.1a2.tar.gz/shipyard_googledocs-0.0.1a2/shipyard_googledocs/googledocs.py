import json
import logging
import re
from typing import Optional
from functools import cached_property
from googleapiclient.discovery import build
from shipyard_templates import Documents, ExitCodeException
from shipyard_googledocs import exceptions
from google.auth import load_credentials_from_file
import tempfile
import os

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
logger = logging.getLogger(__name__)


class GoogleDocsClient(Documents):
    """Client for authenticating and interacting with the Google Docs API."""

    def __init__(
        self,
        service_account_credential: str,
    ) -> None:
        """
        Initializes the GoogleDocsClient.

        Args:
            service_account_credential: Either a path to a credential file or a raw JSON string.

        Raises:
            ExitCodeException: If neither valid file path nor JSON is provided.
        """
        self.service_account_credential = service_account_credential

    @cached_property
    def credentials(self):
        """
        Resolves and returns the appropriate Google credentials object.

        Returns:
            google.auth.credentials.Credentials: Authenticated credentials object.

        Raises:
            ExitCodeException: If credential parsing or loading fails.
        """
        credential_file_path, temp_path = None, None
        try:
            info = json.loads(self.service_account_credential)
            if isinstance(info, dict):
                fd, temp_path = tempfile.mkstemp(suffix=".json")
                logger.info(f"Storing JSON credentials temporarily at {temp_path}")
                with os.fdopen(fd, "w") as tmp:
                    tmp.write(self.service_account_credential)
                credential_file_path = temp_path
                logger.debug("Loaded credentials from JSON string via temporary file.")
        except (ValueError, TypeError):
            if not os.path.exists(self.service_account_credential):
                raise ExitCodeException(
                    f"Provided service_account is neither valid JSON nor a readable file: {self.service_account_credential}",
                    Documents.EXIT_CODE_UNKNOWN_ERROR,
                )
            else:
                credential_file_path = self.service_account_credential

        try:
            creds, _ = load_credentials_from_file(credential_file_path, scopes=SCOPES)
            logger.debug(f"Loaded Credentials from file at: {credential_file_path}")
        except Exception as e:
            raise ExitCodeException(
                f"Failed to load credentials from {credential_file_path}: {str(e)}",
                Documents.EXIT_CODE_UNKNOWN_ERROR,
            )
        finally:
            if temp_path:
                os.remove(temp_path)
                logger.debug(f"Deleted temporary credentials file {temp_path}")

        return creds

    @cached_property
    def docs_service(self):
        """
        Lazily builds and returns the Google Docs service client.

        Returns:
            Resource: A Google Docs API service resource object.
        """
        return build("docs", "v1", credentials=self.credentials)

    @cached_property
    def drive_service(self):
        """
        Lazily builds and returns the Google Drive service client.

        Returns:
            Resource: A Google Drive API service resource object.
        """
        return build("drive", "v3", credentials=self.credentials)

    def fetch(self, doc_url: str) -> str:
        """
        Downloads and returns the full text content of a Google Doc.

        Args:
            doc_url: A full Google Docs URL (e.g., https://docs.google.com/document/d/...).

        Returns:
            str: The full text content of the document.

        Raises:
            InvalidDocUrlError: If the URL is malformed.
            DownloadError: If the document is inaccessible or empty.
        """
        doc_id = self.extract_doc_id_from_url(doc_url)
        if not doc_id:
            raise exceptions.InvalidDocUrlError(doc_url)

        try:
            doc = self.docs_service.documents().get(documentId=doc_id).execute()
            content = []

            for element in doc.get("body", {}).get("content", []):
                paragraph = element.get("paragraph")
                if paragraph:
                    text = "".join(
                        run.get("textRun", {}).get("content", "")
                        for run in paragraph.get("elements", [])
                    )
                    content.append(text)

            full_text = "\n".join(content)
            if not full_text.strip():
                logger.error(f"Google Doc '{doc_id}' is empty. Nothing to download.")
                raise exceptions.DownloadError(doc_id, err_msg="Document is empty.")

            return full_text

        except Exception as e:
            logger.error(f"Error fetching Doc {doc_id}: {e}")
            raise exceptions.DownloadError(doc_id, err_msg=str(e))

    @staticmethod
    def extract_doc_id_from_url(doc_url: str) -> Optional[str]:
        """
        Extracts the document ID from a Google Docs URL.

        Args:
            doc_url: The full Google Docs URL.

        Returns:
            str or None: The extracted document ID, or None if not found.
        """
        match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", doc_url)
        if match:
            doc_id = match.group(1)
            logger.info(f"Extracted document ID: {doc_id}")
            return doc_id
        logger.warning(f"Could not extract document ID from URL: {doc_url}")
        return None

    def upload(self):
        """
        Placeholder method for uploading content to Google Docs.

        Currently unimplemented.
        """
        pass

    def connect(self):
        """
        Verifies that the Docs and Drive service clients are constructed
        without error.

        Returns:
            int: 0 if services were successfully built, 1 otherwise.
        """
        try:
            _ = self.docs_service
            _ = self.drive_service
            return 0
        except Exception as e:
            logger.error(f"Error in connecting to Google Docs API: {e}")
            return 1
