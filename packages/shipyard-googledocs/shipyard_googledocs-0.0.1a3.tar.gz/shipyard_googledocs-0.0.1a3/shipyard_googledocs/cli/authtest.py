# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "shipyard_googledocs",
#     "shipyard-templates>=0.9.0"
# ]
# ///
import sys
import os
from shipyard_templates import ShipyardLogger
from shipyard_googledocs import GoogleDocsClient

logger = ShipyardLogger.get_logger()


def main():
    try:
        sys.exit(
            GoogleDocsClient(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")).connect()
        )
    except Exception as e:
        logger.authtest(f"Could not authenticate Google Docs client due to: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
