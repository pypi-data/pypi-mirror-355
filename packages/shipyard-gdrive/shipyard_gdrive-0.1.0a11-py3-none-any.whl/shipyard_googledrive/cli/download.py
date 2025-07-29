import sys
import argparse

from shipyard_templates import ExitCodeException, ShipyardLogger
from shipyard_googledrive import GoogleDriveClient
from shipyard_bp_utils import files

logger = ShipyardLogger().get_logger()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-file-name-match-type",
        dest="source_file_name_match_type",
        choices={"exact_match", "regex_match"},
        required=False,
    )
    parser.add_argument(
        "--source-folder-name", dest="source_folder_name", default="", required=False
    )
    parser.add_argument("--source-file-name", dest="source_file_name", required=True)
    parser.add_argument(
        "--destination-file-name",
        dest="destination_file_name",
        default="",
        required=False,
    )
    parser.add_argument(
        "--destination-folder-name",
        dest="destination_folder_name",
        default="",
        required=False,
    )
    parser.add_argument(
        "--service-account",
        dest="service_account",
        required=False,
    )
    parser.add_argument("--drive", dest="drive", default="", required=False)
    return parser.parse_args()


def main():
    args = get_args()
    files.combine_folder_and_file_name(
        args.destination_folder_name, args.destination_file_name
    )
    dest_file_name = (
        args.destination_file_name if args.destination_file_name != "" else None
    )

    client = GoogleDriveClient(service_account_credential=args.service_account)

    try:
        drive_id = client.get_drive_id(drive_id=args.drive) if args.drive else None
        folder_id = client.get_folder_id(
            folder_identifier=args.source_folder_name, drive_id=drive_id
        )
        if args.destination_folder_name:
            files.create_folder_if_dne(args.destination_folder_name)

        # for downloading multiple file names
        if args.source_file_name_match_type == "regex_match":
            drive_files = client.get_file_matches(
                pattern=args.source_file_name,
                folder_id=folder_id,
                drive_id=drive_id,
            )

            logger.info(f"Found {len(drive_files)} files, preparing to download...")
            for index, file in enumerate(drive_files):
                file_id = file["id"]
                file_name = file["name"]
                # rename the file appropriately
                dest_name = files.determine_destination_file_name(
                    source_full_path=file_name,
                    destination_file_name=dest_file_name,
                    file_number=index,
                )
                client.download(
                    file_id=file_id,
                    drive_file_name=file_name,
                    destination_file_name=dest_name,
                    drive=drive_id,
                    drive_folder=folder_id,
                )
                logger.info(f"Processed {dest_name}")
        # for single file downloads
        else:  # handles the case for exact_match, any other option will receive an argument error
            file_id = client.get_file_id(
                file_name=args.source_file_name,
                drive_id=drive_id,
                folder_id=folder_id,
            )
            if not file_id:
                logger.error(
                    f"File {args.source_file_name} not found or is not accessible to the service account. Ensure that the file exists in Google Drive and is shared with the service account"
                )
                sys.exit(client.EXIT_CODE_FILE_ACCESS_ERROR)

            client.download(
                file_id=file_id,
                drive_file_name=args.source_file_name,
                destination_file_name=files.combine_folder_and_file_name(
                    folder_name=args.destination_folder_name,
                    file_name=dest_file_name,
                ),
                drive=drive_id,
                drive_folder=folder_id,
            )

    except ExitCodeException as ec:
        logger.error(ec.message)
        sys.exit(ec.exit_code)

    except Exception as e:
        logger.error(f"Error in downloading the file from Google Drive due to {str(e)}")
        sys.exit(client.EXIT_CODE_UNKNOWN_ERROR)

    else:
        logger.info("Successfully downloaded file(s) from Google Drive")


if __name__ == "__main__":
    main()
