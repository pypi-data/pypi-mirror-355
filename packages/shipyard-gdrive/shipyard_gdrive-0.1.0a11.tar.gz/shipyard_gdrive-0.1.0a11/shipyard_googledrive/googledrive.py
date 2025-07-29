import json
import tempfile
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from shipyard_templates import CloudStorage, ExitCodeException
from typing import Optional, Union, List, Any
from googleapiclient.http import MediaIoBaseDownload
from functools import cached_property
from google.auth import load_credentials_from_file
import re

from shipyard_templates import ShipyardLogger

logger = ShipyardLogger.get_logger()


class GoogleDriveClient(CloudStorage):
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    EXIT_CODE_DRIVE_ACCESS_ERROR = 209

    def __init__(
        self,
        service_account_credential: str,
    ) -> None:
        self.service_account_credential = service_account_credential

    @cached_property
    def credentials(self):
        credential_file_path, temp_path = None, None
        try:
            json.loads(self.service_account_credential)

            fd, temp_path = tempfile.mkstemp(suffix=".json")
            logger.info(f"Storing JSON credentials temporarily at {temp_path}")
            with os.fdopen(fd, "w") as tmp:
                tmp.write(self.service_account_credential)
            credential_file_path = temp_path

            logger.debug("Loaded Credentials from JSON string via temporary file.")

        except (ValueError, TypeError) as e:
            logger.debug(
                f"Failed to parse service_account_credential as JSON: {e}. "
                "Assuming it is a file path."
            )
            if not os.path.exists(self.service_account_credential):
                raise ExitCodeException(
                    f"Provided service_account_credential is neither valid JSON "
                    f"nor a readable file",
                    CloudStorage.EXIT_CODE_INVALID_CREDENTIALS,
                )
            else:
                credential_file_path = self.service_account_credential

        creds, _ = load_credentials_from_file(credential_file_path, scopes=self.SCOPES)
        logger.debug(f"Loaded Credentials from file at: {credential_file_path}")
        if temp_path:
            os.remove(temp_path)
            logger.debug(f"Deleted temporary credentials file {temp_path}")

        return creds

    @cached_property
    def service(self):
        """
        Read‐only property returning the Google Drive API client.
        """
        try:
            return build("drive", "v3", credentials=self.credentials)
        except Exception as e:
            logger.debug(f"Failed to build Drive service: {e}")
            raise

    def connect(self):
        """
        Simple connectivity test: attempts to access both clients.
        Returns 0 on success, 1 on failure (logging the error).
        """
        try:
            _ = self.service
            return 0
        except Exception as e:
            logger.authtest(f"Failed to connect to Drive API. Response: {e}")
            return 1

    def move(self):
        pass

    def remove(self):
        pass

    def download(
        self,
        file_id: str,
        drive_file_name: str,
        drive_folder: Optional[str] = None,
        drive: Optional[str] = None,
        destination_file_name: Optional[str] = None,
    ):
        """Downloads a file from Google Drive locally

        Args:
            file_id: The ID of the file to download
            drive_file_name: The name of the file to download
            drive_folder: The optional name of the folder or the ID of folder. If not provided, then it will look for the file within the root directory of the drive
            drive: The optional name or ID of the shared drive
            destination_file_name: The optional name of the downloaded file to have. If not provided, then the file will have the same name as it did in Google Drive
        """
        if drive:
            self.drive_id = self.get_drive_id(drive_id=drive)

        if drive_folder:
            try:
                self.folder_id = self.get_folder_id(
                    folder_identifier=drive_folder,
                    drive_id=self.drive_id,
                )
            except ExitCodeException as ec:
                raise ExitCodeException(ec.message, ec.exit_code)

        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = open(destination_file_name, "wb")
            downloader = MediaIoBaseDownload(fh, request)
            complete = False
            while not complete:
                status, complete = downloader.next_chunk()
        except Exception as e:
            raise ExitCodeException(
                message=str(e), exit_code=self.EXIT_CODE_DOWNLOAD_ERROR
            )
        else:
            return

    def get_all_folder_ids(self, drive_id: Optional[str] = None) -> List[Any]:
        # Set the query to retrieve all folders
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"

        # Execute the query to get the list of folders
        if drive_id:
            folders = self.list_files(query, drive_id=drive_id)
        else:
            folders = self.list_files(query)
        # Extract and return the folder IDs
        folder_ids = [folder["id"] for folder in folders]
        # folder_ids.append('root') # add so that the files not within a folder will be returned as well
        return folder_ids

    def get_file_matches(
        self,
        pattern: str,
        folder_id: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> List[Any]:
        """Helper function to return all the files that match a particular pattern

        Args:
            pattern: The pattern to search for
            folder_id: The folder to search within. If omitted, all file matches across all folders will be returned
            drive_id: The shared drive to search within

        Raises:
            ExitCodeException:

        Returns: The list of the matches

        """
        try:
            files = []
            if folder_id:
                query = f"'{folder_id}' in parents"
                if drive_id:
                    files = self.list_files(query, drive_id=drive_id)
                else:
                    files = self.list_files(query)

            else:
                all_folder_ids = self.get_all_folder_ids(drive_id=drive_id)
                for f_id in all_folder_ids:
                    query = f"'{f_id}' in parents"
                    if drive_id:
                        files.extend(self.list_files(query, drive_id=drive_id))
                    else:
                        files.extend(self.list_files(query))

                # grab the files in the root
                root_query = (
                    "trashed=false and mimeType!='application/vnd.google-apps.folder'"
                )
                if drive_id:
                    root_results = self.list_files(root_query, drive_id=drive_id)
                else:
                    root_results = self.list_files(root_query)
                files.extend(root_results)

            matches = []
            id_set = set()
            for f in files:
                if re.search(pattern, f["name"]) and f["id"] not in id_set:
                    matches.append(f)
                    id_set.add(f["id"])
        except Exception as e:
            raise ExitCodeException(f"Error in finding matching files: {str(e)}", 210)

        else:
            return matches

    def get_drive_id(self, drive_id: str) -> Union[str, None]:
        """Helper function to grab the drive ID when either the name of the drive or the ID is provided. This is instituted for backwards compatibility in the Shipyard blueprint

        Args:
            drive_id:  The name of the drive or the ID from the URL

        Returns: The ID of the drive or None if not found

        """
        try:
            if len(drive_id) == 19 and str(drive_id).startswith("0A"):
                return drive_id
            else:
                results = (
                    self.service.drives()
                    .list(q=f"name = '{drive_id}'", fields="drives(id)")
                    .execute()
                )
                drives = results.get("drives", [])
                if drives:
                    return drives[0]["id"]
                else:
                    return None
        except Exception:
            return None

    def get_folder_id(
        self,
        folder_identifier: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> Union[str, None]:
        """Helper function to grab the folder ID when provided either the name of the folder or the ID (preferred). This is instituted for backwards compatibility in the Shipyard blueprint

        Args:
            drive_id: The optional ID of the shared drive to search within
            folder_identifier: The name of the folder or the ID from the URL

        Returns: The folder ID or None if nonexistent

        """
        if not folder_identifier:
            return None
        try:
            #
            if self.is_folder_id(folder_identifier):
                return folder_identifier
            else:
                folder_names = folder_identifier.split("/")
                tmp_id = "root"  # this will be iteratively updated
                for folder_name in folder_names:
                    if tmp_id == "root":
                        query = f"trashed=false and mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
                    else:
                        query = f"'{tmp_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
                    if not drive_id:
                        folders = self.list_files(query)
                    else:
                        folders = self.list_files(query, drive_id=drive_id)
                    if len(folders) > 1:
                        raise ExitCodeException(
                            f"Multiple folders with name {folder_identifier} found, please use the folder ID instead",
                            204,
                        )
                    if folders:
                        tmp_id = folders[0]["id"]
                    else:
                        return None
                return tmp_id

        except ExitCodeException as ec:
            raise ExitCodeException(ec.message, ec.exit_code)
        except Exception:
            return None

    def create_remote_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None,
        drive_id: Optional[str] = None,
    ) -> str:
        """Helper function to create a folder in Google Drive

        Args:
            folder_name: The name of the folder to create
            parent_id: The optional folder to place the newly created folder within
            drive_id: The optional drive to create the folder in

        Raises:
            ExitCodeException:

        Returns: The ID of the newly created folder

        """
        body = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            body["parents"] = [parent_id]
        if drive_id and not parent_id:
            body["parents"] = [drive_id]

        try:
            folder = (
                self.service.files()
                .create(body=body, supportsAllDrives=True, fields=("id"))
                .execute()
            )
        except Exception as e:
            raise ExitCodeException(
                f"Failed to create folder {folder_name} in Goolge Drive", 208
            )
        return folder["id"]

    def create_remote_folders(self, folder_path: str, drive_id: Optional[str] = None):
        folders = os.path.normpath(folder_path).split(os.sep)
        parent_id = drive_id or "root"

        for folder_name in folders:
            query = (
                f"'{parent_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"name='{folder_name}' and trashed=false"
            )

            params = {
                "q": query,
                "fields": "files(id, name)",
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            }

            if drive_id:
                params["corpora"] = "drive"
                params["driveId"] = drive_id
            else:
                params["corpora"] = "user"

            results = self.service.files().list(**params).execute()
            folders = results.get("files", [])

            if folders:
                parent_id = folders[0]["id"]
            else:
                parent_id = self.create_remote_folder(
                    folder_name=folder_name, parent_id=parent_id, drive_id=drive_id
                )
                logger.info(f"Created folder: {folder_name} (ID: {parent_id})")

        return parent_id

    def get_file_id(
        self,
        file_name: str,
        drive_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Union[str, None]:
        """Helper function to retrieve the file id in Google Drive

        Args:
            file_name: The name of the file to lookup in Google Drive
            drive_id: The Optional ID of the drive
            folder_id: The optional ID of the folder. This is only necessary if the file resides in a folder

        Raises:
            ExitCodeException:

        Returns: The ID of the file if exists, otherwise None

        """
        query = f"name='{file_name}'"
        if folder_id:
            query += f"and '{folder_id}' in parents"
        try:
            if drive_id:
                results = self.list_files(query, drive_id=drive_id)
            else:
                results = self.list_files(query)

        except Exception as e:
            raise ExitCodeException(
                f"Error in fetching file id: {str(e)}", exit_code=203
            )

        return results[0]["id"] if results else None

    def does_file_exist(
        self,
        parent_folder_id: str,
        file_name: str,
        drive_id: Optional[str] = None,
    ) -> bool:
        """Helper function to see if the file already exists in the accessible Google Drive

        Args:
            parent_folder_id: The ID of the parent folder
            file_name: The name of the file
            drive_id: The optional ID of the shared drive

        Returns: True if exists, False if not

        """
        query = f"'{parent_folder_id}' in parents and name='{file_name}'"
        try:
            if drive_id:
                results = self.list_files(query, drive_id=drive_id)
            else:
                results = self.list_files(query)
            return bool(results)

        except Exception as e:
            logger.debug(
                f"An exception was thrown and now file was found, returning False: {str(e)}"
            )
            return False

    @staticmethod
    def is_folder_id(folder_identifier: str) -> bool:
        """Helper function to determine if the input is a legitimate folder ID or a folder name

        Args:
            folder_identifier: Either the folder name or the ID from the URL

        Returns: True if the format matches that of a folder ID, false otherwise

        """
        #  every folder ID starts with 1 and is 33 chars long
        if len(folder_identifier) == 33 and str(folder_identifier).startswith("1"):
            return True
        return False

    def list_files(
        self,
        query,
        drive_id: Optional[str] = None,
    ) -> List[Any]:
        """List files in Google Drive based on a query.

        Args:
            query: The query to filter files.
            drive_id: The optional ID of the shared drive.

        Returns:
            A list of files matching the query.
        """

        if drive_id:
            results = (
                self.service.files()
                .list(
                    q=query,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora="drive",
                    driveId=drive_id,
                    fields="files(id)",
                )
                .execute()
            )
        else:
            results = self.service.files().list(q=query).execute()
        return results.get("files", [])

    def _resolve_folder_id(
        self, drive_folder: Optional[str], drive_id: Optional[str]
    ) -> Optional[str]:
        """
        Resolves or creates the target folder ID.
        """
        folder_id = None
        if drive_folder:
            folder_details = self.get_folder_by_name(drive_folder, drive_id)
            if folder_details:
                folder_id = folder_details.get("id")
            if not folder_id and not self.is_folder_id(drive_folder):
                folder_id = self.create_remote_folders(
                    folder_path=drive_folder,
                    drive_id=drive_id,
                )
        return folder_id

    @staticmethod
    def _build_file_metadata(
        drive_file_name: str, folder_id: Optional[str], drive_id: Optional[str]
    ) -> dict:
        """
        Builds the file metadata for upload or update.
        """
        file_metadata = {
            "name": drive_file_name,
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]
        elif drive_id:
            file_metadata["parents"] = [drive_id]
        else:
            file_metadata["parents"] = ["root"]
        return file_metadata

    def _get_existing_file_id(
        self, drive_file_name: str, drive_id: Optional[str], folder_id: Optional[str]
    ) -> str:
        """
        Gets the file ID of an existing file.
        """
        return self.get_file_id(
            file_name=drive_file_name,
            drive_id=drive_id,
            folder_id=folder_id,
        )

    def _update_file(
        self, file_id: str, file_metadata: dict, media: MediaFileUpload, folder_id: str
    ) -> dict:
        """
        Updates an existing file in Drive.
        """

        try:
            if "parents" in file_metadata:
                del file_metadata["parents"]

            return (
                self.service.files()
                .update(
                    fileId=file_id,
                    body=file_metadata,
                    media_body=media,
                    supportsAllDrives=True,
                    fields="id",
                    addParents=folder_id,
                )
                .execute()
            )

        except Exception as e:
            raise ExitCodeException(
                f"Failed to update file {file_id}: {self._format_error_message(e)}",
                self.EXIT_CODE_UPLOAD_ERROR,
            )

    def _create_file(self, file_metadata: dict, media: MediaFileUpload) -> dict:
        """
        Creates a new file in Drive.
        """
        try:
            return (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    supportsAllDrives=True,
                    fields="id",
                )
                .execute()
            )
        except Exception as e:
            raise ExitCodeException(
                f"Failed to create file: {self._format_error_message(e)}",
                self.EXIT_CODE_UPLOAD_ERROR,
            )

    def upload(
        self,
        file_path: str,
        drive_folder: Optional[str] = None,
        drive_id: Optional[str] = None,
        drive_file_name: Optional[str] = None,
    ) -> str:
        """
        Uploads or updates a file to Google Drive (including Shared Drives).
        """
        if not os.path.exists(file_path):
            raise ExitCodeException(
                f"File {file_path} does not exist",
                self.EXIT_CODE_FILE_NOT_FOUND,
            )
        try:
            folder_id = None
            if drive_id:
                drive_id = self.get_drive_id(drive_id=drive_id)
                if not drive_id:
                    raise ExitCodeException(
                        f"Drive with ID '{drive_id}' not found or not accessible.",
                        self.EXIT_CODE_DRIVE_ACCESS_ERROR,
                    )
            if drive_folder:
                folder_id = self._resolve_folder_id(drive_folder, drive_id)

            drive_file_name = drive_file_name or os.path.basename(file_path)
            file_metadata = self._build_file_metadata(
                drive_file_name, folder_id, drive_id
            )

            media = MediaFileUpload(file_path, resumable=True)
            file_exists = self.does_file_exist(
                parent_folder_id=folder_id, file_name=drive_file_name, drive_id=drive_id
            )

            if file_exists:
                file_id = self.get_file_id(drive_file_name, drive_id, folder_id)
                logger.info(
                    f"File '{drive_file_name}' exists. Updating file {file_id}..."
                )
                upload_file = self._update_file(
                    file_id, file_metadata, media, folder_id
                )
                logger.info(f"Updated file ID: {upload_file.get('id')}")
            else:
                logger.info(
                    f"File '{drive_file_name}' does not exist. Creating new file..."
                )
                upload_file = self._create_file(file_metadata, media)
                logger.info(f"Created new file ID: {upload_file.get('id')}")

            return upload_file.get("id")

        except FileNotFoundError as fe:
            raise ExitCodeException(
                message=str(fe), exit_code=self.EXIT_CODE_FILE_NOT_FOUND
            )
        except ExitCodeException as ec:
            raise ExitCodeException(message=ec.message, exit_code=ec.exit_code)
        except Exception as e:
            raise ExitCodeException(
                message=f"Error uploading file to Google Drive. Error Code: {e}",
                exit_code=self.EXIT_CODE_UPLOAD_ERROR,
            )

    def list_folders(self):
        """
        Lists all folders in the Google Drive.
        Returns a list of folder names and their IDs.
        """

        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        folders = self.list_files(query)
        return [{"name": folder["name"], "id": folder["id"]} for folder in folders]

    def get_folder_by_name(self, folder_name, drive_id=None):
        """
        Finds a Google Drive folder by its name.

        Args:
            folder_name (str): The name of the folder to search for.
            drive_id (str, optional): The ID of the Shared Drive (if applicable). If None, searches My Drive.

        Returns:
            dict: A dictionary with folder 'id' and 'name', or None if not found.
        """

        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

        params = {
            "q": query,
            "fields": "files(id, name)",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
        }

        if drive_id:
            params["corpora"] = "drive"
            params["driveId"] = drive_id
        else:
            params["corpora"] = "user"

        results = self.service.files().list(**params).execute()
        folders = results.get("files", [])

        if not folders:
            logger.warning(f"No folder found with name: {folder_name}")
            return None
        else:
            folder = folders[0]
            logger.info(f"Found folder: {folder['name']} (ID: {folder['id']})")
            return folder

    @staticmethod
    def _format_error_message(e: Exception) -> str:
        """
        Formats the error message for exceptions.
        """
        if hasattr(e, "status_code") and hasattr(e, "reason"):
            return f"{e.status_code} - {e.reason}"
        else:
            return str(e)
