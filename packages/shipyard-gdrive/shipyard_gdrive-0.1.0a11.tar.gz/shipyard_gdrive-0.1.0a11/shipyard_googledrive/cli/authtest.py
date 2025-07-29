# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "shipyard-gdrive",
# ]
# ///
import os
import sys
from shipyard_googledrive import GoogleDriveClient


def main():
    sys.exit(GoogleDriveClient(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")).connect())


if __name__ == "__main__":
    main()
