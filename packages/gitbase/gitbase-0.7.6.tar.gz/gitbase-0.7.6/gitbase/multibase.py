"""
The 'MultiBase' extension of the 'GitBase' module: Allows using multiple GitBase instances in sequence when one becomes full. It provides methods to write, read, delete, upload, and download data across multiple GitBase instances, switching between them if needed.

Consists of: 
* MultiBase (class): A class that manages multiple GitBase instances and distributes actions across them when one instance is full.
    - param: gitbases (List[Dict[str, str]]): A list of GitBase configurations with 'token', 'repo_owner', 'repo_name', and 'branch'.

    Methods:
        - _get_active_gitbase() -> Optional['GitBase']: Returns the currently active GitBase instance.
            - returns: Optional[GitBase]: The active GitBase instance or `None` if no active instance is available.

        - _switch_to_next_gitbase() -> bool: Switches to the next GitBase if available.
            - returns: bool: `True` if the switch is successful, `False` if there are no more GitBase instances.

        - write_data(path: str, data: str, message: str = "Updated data") -> int: Writes data to the first available GitBase, switching if needed.
            - param: path (str): The path where the data will be written.
            - param: data (str): The data to write.
            - param: message (str): A commit message for the data update.
            - returns: int: The HTTP status code indicating the result (e.g., 200 for success).

        - read_data(path: str) -> Tuple[Optional[str], Optional[str]]: Reads data from the first GitBase where the file exists.
            - param: path (str): The path to the file to read.
            - returns: Tuple[Optional[str], Optional[str]]: A tuple with the file content and SHA, or `None, None` if the file does not exist.

        - delete_data(path: str, message: str = "Deleted data") -> int: Deletes data from all GitBase instances.
            - param: path (str): The path to the data to delete.
            - param: message (str): A commit message for the deletion.
            - returns: int: The HTTP status code indicating the result (e.g., 200 for success, 404 for not found).

        - upload_file(file_path: str, remote_path: str, message: str = "Uploaded file") -> int: Uploads a file using the first available GitBase, switching if needed.
            - param: file_path (str): The local path to the file.
            - param: remote_path (str): The remote path where the file will be uploaded.
            - param: message (str): A commit message for the upload.
            - returns: int: The HTTP status code indicating the result (e.g., 200 for success).

        - download_file(remote_path: str, local_path: str) -> int: Downloads a file from the first GitBase where it exists.
            - param: remote_path (str): The path to the remote file.
            - param: local_path (str): The local path where the file will be saved.
            - returns: int: The HTTP status code indicating the result (e.g., 200 for success, 404 for not found).

        - get_file_last_modified(path: str) -> Optional[float]: Returns the latest modified timestamp across all GitBase instances.
            - param: path (str): The path to the file.
            - returns: Optional[float]: The latest modified timestamp, or `None` if no valid timestamps are available.
"""

import requests
import base64
from typing import Optional, Tuple, List, Dict, Union
from datetime import datetime
from .gitbase import GitBase

from typing import List, Dict, Tuple, Optional
import requests
import base64
from datetime import datetime

class MultiBase:
    def __init__(self, gitbases: List[Dict[str, str]]) -> None:
        self.gitbases = [GitBase(**gb) for gb in gitbases]
        self.current_index = 0

    def _get_active_gitbase(self) -> Optional['GitBase']:
        if self.current_index < len(self.gitbases):
            return self.gitbases[self.current_index]
        return None

    def _switch_to_next_gitbase(self) -> bool:
        if self.current_index + 1 < len(self.gitbases):
            self.current_index += 1
            return True
        return False
    
    def __getattr__(self, attr):
        gitbase = self._get_active_gitbase()
        if gitbase and hasattr(gitbase, attr):
            return getattr(gitbase, attr)
        raise AttributeError(f"'MultiBase' object has no attribute '{attr}'")

    # Forward internal method to the current gitbase
    def _get_file_url(self, path: str) -> Optional[str]:
        gitbase = self._get_active_gitbase()
        if gitbase:
            return gitbase._get_file_url(path)
        return None

    def _get_file_content(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        # Search all gitbases for first with content
        for gitbase in self.gitbases:
            content, sha = gitbase._get_file_content(path)
            if content is not None:
                return content, sha
        return None, None

    # Public API methods (same signatures)

    def read_data(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        for gitbase in self.gitbases:
            content, sha = gitbase.read_data(path)
            if content is not None:
                return content, sha
        return None, None

    def write_data(self, path: str, data: str, message: str = "Updated data") -> int:
        while self.current_index < len(self.gitbases):
            gitbase = self._get_active_gitbase()
            if gitbase:
                status = gitbase.write_data(path, data, message)
                if status in {200, 201}:
                    return status
                if not self._switch_to_next_gitbase():
                    return status
        return 507

    def delete_data(self, path: str, message: str = "Deleted data") -> int:
        status_codes = [gb.delete_data(path, message) for gb in self.gitbases]
        return 200 if any(status == 200 for status in status_codes) else 404

    def upload_file(self, file_path: str, remote_path: str, message: str = "Uploaded file") -> int:
        while self.current_index < len(self.gitbases):
            gitbase = self._get_active_gitbase()
            if gitbase:
                status = gitbase.upload_file(file_path, remote_path, message)
                if status in {200, 201}:
                    return status
                if not self._switch_to_next_gitbase():
                    return status
        return 507

    def download_file(self, remote_path: str, local_path: str) -> int:
        for gitbase in self.gitbases:
            status = gitbase.download_file(remote_path, local_path)
            if status == 200:
                return status
        return 404

    def get_file_last_modified(self, path: str) -> Optional[float]:
        timestamps = [gb.get_file_last_modified(path) for gb in self.gitbases]
        valid_ts = [ts for ts in timestamps if ts is not None]
        return max(valid_ts, default=None)

    def get_all_keys(self, path: str) -> List[str]:
        for gitbase in self.gitbases:
            keys = gitbase.get_all_keys(path)
            if keys:
                return keys
        return []

    def data_loaded(self) -> bool:
        return any(gb.data_loaded() for gb in self.gitbases)

    def is_online(self, url='http://www.google.com', timeout=5) -> bool:
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    @staticmethod
    def generate_example() -> None:
        # Static method forwarding to GitBase (pick the first one or GitBase class itself)
        GitBase.generate_example()