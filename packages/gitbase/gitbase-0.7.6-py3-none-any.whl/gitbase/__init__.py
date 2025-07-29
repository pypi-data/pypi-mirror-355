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
- data_loaded() -> bool:
    Checks whether data has been successfully loaded.
    - returns: True if data has been loaded, False otherwise.

- init(show_credits: bool = True) -> None:
    Initializes the GitBase module, displaying credits if enabled.
    - param show_credits (bool): Whether to display credits.
    
---

The 'DataSystem' extension of the 'GitBase' module: Allows for general data management excluding account/player data management.

Consists of: 
* KeyValue (class): Represents a key-value pair for storing data.
    - param: key (str): The key to represent the pair.
    - param: value (Any): The value connected to the key. Can be anything.

* DataSystem (class): Handles data storage and retrieval, supporting online GitBase and offline backups.
    - param: db (GitBase): The database object for interacting with GitBase.
    - param: encryption_key (bytes): Key for encrypting and decrypting data.
    - param: fernet (Fernet): Encryption handler from the `cryptography` package.
    
    Methods:
        - encrypt_data(data: str) -> bytes: Encrypts a string using the configured encryption key.
            - param: data (str): The plaintext string to encrypt.
            - returns: bytes: The encrypted data as bytes.

        - decrypt_data(encrypted_data: bytes) -> str: Decrypts a string using the configured encryption key.
            - param: encrypted_data (bytes): The encrypted data to decrypt.
            - returns: str: The decrypted plaintext string.

        - save_data(key: str, value: Any, path: str = "data", encryption: bool = False) -> None: 
            Saves data to GitBase or an offline backup.
            - param: key (str): The key to associate with the data.
            - param: value (Any): The value to save.
            - param: path (str): The directory path to save the data in.
            - param: encryption (bool): Whether to encrypt the data before saving.

        - load_data(key: str, encryption: bool, path: str = "data") -> Optional[Any]: 
            Loads data from GitBase or an offline backup.
            - param: key (str): The key of the data to load.
            - param: encryption (bool): Whether to decrypt the data after loading.
            - param: path (str): The directory path to load the data from.
            - returns: Optional[Any]: The loaded data, or None if not found.

        - use_offline_data(key: str, value: Any) -> None: 
            Saves data to an offline backup file.
            - param: key (str): The key to associate with the data.
            - param: value (Any): The value to save.

        - use_offline_data(key: str) -> Optional[Any]: 
            Loads data from an offline backup file.
            - param: key (str): The key of the data to load.
            - returns: Optional[Any]: The loaded data, or None if not found.

        - delete_data(key: str, path: str = "data", delete_offline: bool = False) -> None: 
            Deletes data from GitBase and optionally from offline storage.
            - param: key (str): The key of the data to delete.
            - param: path (str): The path to the data.
            - param: delete_offline (bool): Whether to delete the offline backup as well.

        - get_all(path: str = "data") -> Dict[str, Any]: 
            Retrieves all key-value pairs stored in the system.
            - param: path (str): The directory path to retrieve data from.
            - returns: Dict[str, Any]: A dictionary of all key-value pairs.

        - chunk(file_path: str, output_dir: str, duration_per_chunk: int = 90) -> None: 
            Splits a video file into smaller chunks.
            - param: file_path (str): Path to the input video file.
            - param: output_dir (str): Directory to save the video chunks.
            - param: duration_per_chunk (int): Duration per chunk in seconds.
            - Notes: Ensures a minimum of 4 chunks.

        - pack(chunks_dir: str, output_file: str) -> None: 
            Combines video chunks into a single file.
            - param: chunks_dir (str): Directory containing the video chunks.
            - param: output_file (str): Path for the combined output file.
            - Notes: Assumes chunks are in order and in the same format.

        - partial_pack(chunks_dir: str, output_file: str, start_chunk: int, end_chunk: int) -> None: 
            Combines a range of video chunks into a single file.
            - param: chunks_dir (str): Directory containing the video chunks.
            - param: output_file (str): Path for the combined output file.
            - param: start_chunk (int): Starting chunk number.
            - param: end_chunk (int): Ending chunk number.
            - Notes: Assumes chunks are in order and in the same format.
            
---

The 'PlayerDataSystem' extension of the 'GitBase' module: Manages player account data with support for online storage via GitBase and offline backups.

Consists of: 
* PlayerDataSystem (class): Handles player data storage, retrieval, and encryption, supporting GitBase for online persistence and local backups.
    - param: db (GitBase): The database object for interacting with GitBase.
    - param: encryption_key (bytes): Key for encrypting and decrypting player data.
    - param: fernet (Fernet): Encryption handler from the `cryptography` package.

    Methods:
        - encrypt_data(data: str) -> bytes: Encrypts a string using the configured encryption key.
            - param: data (str): The plaintext string to encrypt.
            - returns: bytes: The encrypted data as bytes.

        - decrypt_data(encrypted_data: bytes) -> str: Decrypts a string using the configured encryption key.
            - param: encrypted_data (bytes): The encrypted data to decrypt.
            - returns: str: The decrypted plaintext string.

        - save_account(username: str, player_instance: Any, encryption: bool, attributes: Optional[List[str]] = None, path: str = "players") -> None: 
            Saves a player's account data to GitBase or an offline backup.
            - param: username (str): The player's username.
            - param: player_instance (Any): The player instance containing data to save.
            - param: encryption (bool): Whether to encrypt the data before saving.
            - param: attributes (Optional[List[str]]): Specific attributes to save; defaults to all.
            - param: path (str): The directory path to save the data in.

        - use_offline_account(username: str, player_instance: Any, attributes: Optional[List[str]] = None) -> None: 
            Saves player data to an offline backup file.
            - param: username (str): The player's username.
            - param: player_instance (Any): The player instance containing data to save.
            - param: attributes (Optional[List[str]]): List of attributes to save; defaults to all.

        - load_account(username: str, player_instance: Any, encryption: bool) -> None: 
            Loads a player's account data from GitBase or an offline backup.
            - param: username (str): The player's username.
            - param: player_instance (Any): The player instance to populate with data.
            - param: encryption (bool): Whether to decrypt the data after loading.

        - use_offline_account(username: str, player_instance: Any) -> None: 
            Loads player data from an offline backup file.
            - param: username (str): The player's username.
            - param: player_instance (Any): The player instance to populate with data.

        - delete_account(username: str, delete_offline: bool = False) -> None: 
            Deletes a player's account data from GitBase and optionally from offline storage.
            - param: username (str): The player's username.
            - param: delete_offline (bool): Whether to delete the offline backup as well.

        - get_all(path: str = "players") -> Dict[str, Any]: 
            Retrieves all stored player accounts.
            - param: path (str): The directory path to retrieve data from.
            - returns: Dict[str, Any]: A dictionary of all player accounts.

---

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

---

The 'ProxyFile' extension of the 'GitBase' module: Allows streaming of remote files stored in a GitHub repository. This is useful for working with large files or media, as it avoids the need for downloading the entire file before usage. Supports streaming of audio and video files directly from GitHub.

Consists of: 
* ProxyFile (class): A class designed to facilitate streaming files from a GitHub repository using GitHub's raw content API.
    - param: repo_owner (str): The owner of the GitHub repository.
    - param: repo_name (str): The name of the repository.
    - param: token (str): The GitHub authentication token for accessing private repositories.
    - param: branch (str, optional): The GitHub branch (default is 'main').

    Methods:
        - _get_file_url(path: str) -> str: Constructs the URL to access a file in a GitHub repository.
            - param: path (str): The file's path in the repository.
            - returns: str: The constructed GitHub API URL.

        - _fetch_file(path: str) -> bytes: Fetches the file's content from GitHub without downloading it, returning the content as bytes.
            - param: path (str): The file's path in the repository.
            - returns: bytes: The file content in base64-decoded bytes.

        - get_file(remote_path: str) -> io.BytesIO: Retrieves any file from GitHub as an in-memory stream.
            - param: remote_path (str): The path to the file in the GitHub repository.
            - returns: io.BytesIO: A `BytesIO` object containing the file data.

        - play_audio(remote_path: str) -> None: Streams and plays an audio file (WAV format) directly from GitHub without downloading.
            - param: remote_path (str): The path to the audio file in the repository.

        - play_video(remote_path: str) -> None: Streams and plays a video file (MP4 format) directly from GitHub without downloading.
            - param: remote_path (str): The path to the video file in the repository.
"""
from fancyutil import NotificationManager as nm, init as fancy_init; fancy_init(display_credits=False)
from .gitbase import GitBase, data_loaded, is_online, init
from .playerDataSystem import PlayerDataSystem
from .dataSystem import DataSystem, KeyValue
from .multibase import MultiBase
from .proxyFile import ProxyFile
from .__config__ import config as __config__

# Initialize NotificationManager instance
NotificationManager: nm = nm()

__all__ = [
    "GitBase", "is_online", "data_loaded", 
    "PlayerDataSystem", "DataSystem", "KeyValue", 
    "MultiBase", "NotificationManager", 
    "ProxyFile", "init", "__config__"
]