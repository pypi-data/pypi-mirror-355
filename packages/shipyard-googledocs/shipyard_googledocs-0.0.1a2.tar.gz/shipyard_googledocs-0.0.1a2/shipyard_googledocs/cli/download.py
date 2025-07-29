#!/usr/bin/env python3

import argparse
import os
import socket
import sys
from shipyard_bp_utils import files as shipyard
from shipyard_templates import ShipyardLogger, ExitCodeException, Documents
from shipyard_googledocs import GoogleDocsClient

logger = ShipyardLogger.get_logger()
socket.setdefaulttimeout(600)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-account", dest="service_account", required=False)
    parser.add_argument(
        "--source-file-url",
        dest="file_url",
        required=True,
        help="Full URL to the Google Doc",
    )
    parser.add_argument(
        "--destination-file-name",
        dest="destination_file_name",
        default=None,
        required=True,
        help="Name to save the .txt file locally",
    )
    parser.add_argument(
        "--destination-folder-name",
        dest="destination_folder_name",
        default="",
        required=False,
        help="Optional folder path to save the file",
    )
    return parser.parse_args()


def main():
    try:
        args = get_args()
        doc_url = args.file_url
        destination_folder_name = shipyard.clean_folder_name(args.destination_folder_name)

        if destination_folder_name and not os.path.exists(destination_folder_name):
            os.makedirs(destination_folder_name)

        destination_path = shipyard.combine_folder_and_file_name(
            destination_folder_name, args.destination_file_name
        )

        if len(destination_path.rsplit("/", 1)) > 1:
            path = destination_path.rsplit("/", 1)[0]
            if not os.path.exists(path):
                os.makedirs(path)

        client = GoogleDocsClient(service_account_credential=args.service_account)
        logger.info("Successfully connected to Google Docs client.")
        full_text = client.fetch(doc_url)

        with open(destination_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        file_name = os.path.basename(destination_path)
        logger.info(
            f"Saved document: {file_name} to {destination_path} with {len(full_text)} characters."
        )

    except FileNotFoundError as e:
        logger.error(e)
        sys.exit(Documents.EXIT_CODE_FILE_NOT_FOUND)

    except ExitCodeException as e:
        logger.error(e)
        sys.exit(e.exit_code)

    except Exception as e:
        logger.error(f"An unexpected error occurred\n{e}")
        sys.exit(Documents.EXIT_CODE_UNKNOWN_ERROR)
    else:
        logger.info(f"Download completed successfully to {destination_path}")


if __name__ == "__main__":
    main()
