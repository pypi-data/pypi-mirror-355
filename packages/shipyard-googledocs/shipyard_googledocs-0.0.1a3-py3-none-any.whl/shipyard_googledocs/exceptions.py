from shipyard_templates import ExitCodeException, Documents


class DownloadError(ExitCodeException):
    def __init__(self, doc_id, err_msg=None):
        base = f"Failed to download document '{doc_id}'"
        message = f"{base}: {err_msg}" if err_msg else base
        super().__init__(message, Documents.EXIT_CODE_DOWNLOAD_ERROR)


class InvalidFormatError(ExitCodeException):
    def __init__(self, detail=""):
        message = f"Invalid format{': ' + detail if detail else ''}"
        super().__init__(message, Documents.EXIT_CODE_INVALID_INPUT)


class InvalidCredentialsError(ExitCodeException):
    def __init__(self, detail=""):
        message = f"Invalid credentials{': ' + detail if detail else ''}"
        super().__init__(message, Documents.EXIT_CODE_INVALID_INPUT)


class InvalidDocUrlError(Exception):
    def __init__(self, url):
        super().__init__(
            f"Could not extract document ID from URL: {url}. "
            "Please provide a valid Google Docs URL and ensure you have shared the document "
            "with the client Google service account. "
            "Instructions: https://help.alliplatform.com/actions/Working-version/how-to-find-your-alli-client-s-google-service-acco"
        )
