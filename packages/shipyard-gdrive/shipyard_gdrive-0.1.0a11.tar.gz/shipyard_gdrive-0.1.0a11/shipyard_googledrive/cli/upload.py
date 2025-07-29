import sys
import argparse

from shipyard_templates import ExitCodeException, ShipyardLogger, CloudStorage
from shipyard_googledrive import GoogleDriveClient
from shipyard_bp_utils import files

logger = ShipyardLogger().get_logger()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-account", dest="service_account", required=False)
    parser.add_argument("--drive", required=False, default="")
    parser.add_argument("--source-file-name", dest="source_file_name", required=True)
    parser.add_argument(
        "--source-folder-name", dest="source_folder_name", required=False, default=""
    )
    parser.add_argument(
        "--source-file-name-match-type",
        dest="source_file_name_match_type",
        required=False,
        default="exact_match",
        choices={"exact_match", "regex_match"},
    )
    parser.add_argument(
        "--destination-file-name", dest="destination_file_name", required=False
    )
    parser.add_argument(
        "--destination-folder-name",
        dest="destination_folder_name",
        required=False,
        default="",
    )
    return parser.parse_args()


def main():
    args = get_args()
    try:
        client = GoogleDriveClient(service_account_credential=args.service_account)
        drive_folder = args.destination_folder_name or None
        drive_file_name = args.destination_file_name or None
        drive_name = args.drive or None

        file_matches = files.find_matching_files(
            args.source_file_name,
            args.source_folder_name or "",
            args.source_file_name_match_type,
        )
        if len(file_matches) == 0:
            logger.error(f"No files found matching {args.source_file_name}")
            sys.exit(client.EXIT_CODE_FILE_NOT_FOUND)
        for index, file in enumerate(file_matches, start=1):
            new_file_name = files.determine_destination_file_name(
                source_full_path=file,
                destination_file_name=drive_file_name,
                file_number=index,
            )

            client.upload(
                file_path=file,
                drive_folder=drive_folder,
                drive_id=drive_name,
                drive_file_name=new_file_name,
            )
            logger.info(f"Processed {file}")

    except ExitCodeException as ec:
        logger.error(ec.message)
        sys.exit(ec.exit_code)
    except Exception as e:
        logger.error("Error in uploading file to drive")
        logger.exception(str(e))
        sys.exit(CloudStorage.EXIT_CODE_UPLOAD_ERROR)
    else:
        logger.info("Successfully loaded file(s) to Google Drive!")


if __name__ == "__main__":
    main()
