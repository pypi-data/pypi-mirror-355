"""
GitBase: A module for managing data storage in a GitHub repository, allowing reading, writing, uploading, and deleting files.

Classes:
- GitBase: Handles interactions with a GitHub repository for file storage and retrieval.
    - param token (str): The GitHub access token for authentication.
    - param repo_owner (str): The owner of the GitHub repository.
    - param repo_name (str): The name of the GitHub repository.
    - param branch (str, default='main'): The branch where files are stored.

    Methods:
    - read_data(path: str) -> Tuple[Optional[str], Optional[str]]:
        Reads a file from the repository and returns its content and SHA.
        - param path (str): The file path in the repository.
        - returns: A tuple containing the file content and SHA identifier.

    - write_data(path: str, data: str, message: str = "Updated data") -> int:
        Writes or updates a file in the repository.
        - param path (str): The file path in the repository.
        - param data (str): The data to be written.
        - param message (str): The commit message for the update.
        - returns: HTTP status code of the operation.

    - delete_data(path: str, message: str = "Deleted data") -> int:
        Deletes a file from the repository.
        - param path (str): The file path in the repository.
        - param message (str): The commit message for the deletion.
        - returns: HTTP status code of the operation.

    - upload_file(file_path: str, remote_path: str, message: str = "Uploaded file") -> int:
        Uploads a local file to the repository.
        - param file_path (str): The local file path.
        - param remote_path (str): The target file path in the repository.
        - param message (str): The commit message for the upload.
        - returns: HTTP status code of the operation.

    - download_file(remote_path: str, local_path: str) -> int:
        Downloads a file from the repository to the local system.
        - param remote_path (str): The file path in the repository.
        - param local_path (str): The destination path on the local system.
        - returns: HTTP status code of the operation.

    - get_file_last_modified(path: str) -> Optional[float]:
        Retrieves the last modified timestamp of a file in the repository.
        - param path (str): The file path in the repository.
        - returns: The timestamp of the last modification or None if unavailable.

Functions:
- is_online(url='http://www.google.com', timeout=5) -> bool:
    Checks if the user has an active internet connection.
    - param url (str): The URL to test connectivity.
    - param timeout (int): The request timeout in seconds.
    - returns: True if online, False otherwise.

- data_loaded() -> bool:
    Checks whether data has been successfully loaded.
    - returns: True if data has been loaded, False otherwise.

- init(show_credits: bool = True) -> None:
    Initializes the GitBase module, displaying credits if enabled.
    - param show_credits (bool): Whether to display credits.
"""
import requests
import base64
import os
from typing import Optional, Tuple, Union, Dict, List
from altcolor import cPrint, init; init(show_credits=False)
from datetime import datetime
from time import sleep as wait
global canUse
from .config import canUse

# Define a variable to check if data is loaded/has been found before continuing to try to update any class instances
loaded_data: bool = False

# Define a function to check if the user is online
def is_online(url='http://www.google.com', timeout=5) -> bool:
    """Check if the user is online before continuing code"""
    
    #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
    try:
        response = requests.get(url, timeout=timeout)
        # If the response status code is 200, we have an internet connection
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False

# Get the value of 'loaded_data'
def data_loaded() -> bool:    
    """Get the value of 'loaded_data'"""
    
    #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
    return loaded_data

class GitBase:
    def __init__(self, token: str, repo_owner: str, repo_name: str, branch: str = 'main') -> None:
        self.token: str = token
        self.repo_owner: str = repo_owner
        self.repo_name: str = repo_name
        self.branch: str = branch
        self.headers: Dict[str, str] = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _get_file_url(self, path: str) -> str:
        """Reterive GitHub url for file"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        return f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"

    def _get_file_content(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get the content of a file"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        url: str = self._get_file_url(path)
        response: requests.Response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            file_data: Dict[str, Union[str, bytes]] = response.json()
            sha: str = file_data['sha']
            content: str = base64.b64decode(file_data['content']).decode('utf-8')
            return content, sha
        return None, None

    def read_data(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        """Read a file and return it's data as content and sha"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        content, sha = self._get_file_content(path)
        return content, sha

    def write_data(self, path: str, data: str, message: str = "Updated data") -> int:
        """Write to/update a file's content"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        try:
            url: str = self._get_file_url(path)
            content, sha = self._get_file_content(path)
            encoded_data: str = base64.b64encode(data.encode('utf-8')).decode('utf-8')

            payload: Dict[str, Union[str, None]] = {
                "message": message,
                "content": encoded_data,
                "branch": self.branch
            }

            if sha:
                payload["sha"] = sha

            response: requests.Response = requests.put(url, headers=self.headers, json=payload)
            return response.status_code
        except Exception as e:
            raise Exception(f"Error: {e}")

    def delete_data(self, path: str, message: str = "Deleted data") -> int:
        """Delete data for a file"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        try:
            url: str = self._get_file_url(path)
            _, sha = self._get_file_content(path)

            if sha:
                payload: Dict[str, str] = {
                    "message": message,
                    "sha": sha,
                    "branch": self.branch
                }
                response: requests.Response = requests.delete(url, headers=self.headers, json=payload)
                return response.status_code
            else:
                return 404
        except Exception as e:
            raise Exception(f"Error: {e}")

    @staticmethod
    def generate_example() -> None:
        """Generate an example of how to use GitBase"""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        # Get the directory of the current file (gitbase.py)
        current_dir = os.path.dirname(__file__)
        
        # Construct the full path to example.py
        example_file_path = os.path.join(current_dir, "example.py")
        
        # Read from test.py
        with open(example_file_path, "rb") as file:
            example_code: bytes = file.read()
        
        # Write to example_code.py
        with open("example_code.py", "wb") as file:
            file.write(example_code)

    def upload_file(self, file_path: str, remote_path: str, message: str = "Uploaded file") -> int:
        """Upload a file to the online database."""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        try:
            with open(file_path, "rb") as file:
                encoded_data = base64.b64encode(file.read()).decode('utf-8')

            payload: Dict[str, Union[str, None]] = {
                "message": message,
                "content": encoded_data,
                "branch": self.branch
            }

            url: str = self._get_file_url(remote_path)
            response: requests.Response = requests.put(url, headers=self.headers, json=payload)
            return response.status_code
        except Exception as e:
            raise Exception(f"Error uploading file: {e}")

    def download_file(self, remote_path: str, local_path: str) -> int:
        """Download a file from the online database."""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        try:
            content, _ = self._get_file_content(remote_path)
            if content:
                with open(local_path, "wb") as file:
                    file.write(base64.b64decode(content))
                return 200
            return 404
        except Exception as e:
            raise Exception(f"Error downloading file: {e}")

    def get_file_last_modified(self, path: str) -> Optional[float]:
        """Get the last modified timestamp of the file from the GitHub repository."""
        
        #if not canUse: raise ModuleNotFoundError("No module named 'gitbase'")
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/commits?path={path}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                commits = response.json()
                if commits:
                    # Get the date of the most recent commit
                    last_modified = commits[0]['commit']['committer']['date']
                    return datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        except Exception as e:
            raise Exception(f"Error getting last modified time for {path}: {e}")
        return None
    
    def get_all_keys(self, path: str) -> List[str]:
        """
        Retrieves all keys (file names) from the repository.

        Args:
            path (str): The directory path in the repository.

        Returns:
            List[str]: A list of keys (file names) without extensions.
        """
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            files = response.json()
            return [file['name'].replace('.json', '') for file in files if file['name'].endswith('.json')]
        return []

def init(show_credits: bool = True) -> None:
    """Initialize the GitBase module."""
    
    if show_credits:
        cPrint("BLUE", "\n\nThanks for using GitBase! Check out our other products at 'https://tairerullc.vercel.app'\n\n")
        wait(2)
        
    canUse = True