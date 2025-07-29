import os
import json
from cryptography.fernet import Fernet
from typing import Optional, Union, Dict, Any, List
from altcolor import cPrint
from .gitbase import GitBase, is_online
import requests
global canUse
from .config import canUse
from .__config__ import config as __config__
from .multibase import MultiBase
from typing import Union, Any, Optional
import jsonpickle

class PlayerDataSystem:
    """
    A system for managing player data, utilizing GitBase for online storage and 
    local backups for offline access, with optional encryption support.
    """

    def __init__(self, db: Union[GitBase, MultiBase], encryption_key: bytes) -> None:
        """
        Initialize the PlayerDataSystem.

        Args:
            db (GitBase): The GitBase instance for managing online storage.
            encryption_key (bytes): The encryption key for securing player data.
        """
        self.db: Union[GitBase, MultiBase] = db
        self.encryption_key: bytes = encryption_key
        self.fernet: Fernet = Fernet(self.encryption_key)

    def encrypt_data(self, data: str) -> bytes:
        """
        Encrypt a string using Fernet encryption.

        Args:
            data (str): The string to encrypt.

        Returns:
            bytes: The encrypted data as bytes.
        """
        
        return self.fernet.encrypt(data.encode('utf-8'))

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Decrypt Fernet-encrypted data.

        Args:
            encrypted_data (bytes): The encrypted data to decrypt.

        Returns:
            str: The decrypted string.
        """
        
        return self.fernet.decrypt(encrypted_data).decode('utf-8')

    def save_account(self, username: str, player_instance: Any, encryption: bool, attributes: Optional[List[str]] = None, path: str = "players") -> None:
        """
        Save a player's account data to the database, with optional encryption and local backup.

        Args:
            username (str): The player's username.
            player_instance (Any): The player instance containing data to save.
            encryption (bool): Whether to encrypt the data.
            attributes (Optional[List[str]]): List of attributes to save; defaults to all.
            path (str): The path for saving data; defaults to "players".
        """
        
        try:
            # Extract player data
            if attributes:
                player_data: Dict[str, Union[str, int, float]] = {var: getattr(player_instance, var) for var in attributes if hasattr(player_instance, var)}
            else:
                player_data = jsonpickle.encode(player_instance)

            # Encrypt data if required
            if encryption:
                encrypted_data: str = self.encrypt_data(player_data).decode('utf-8')
            else:
                encrypted_data: str = player_data

            # Format the path
            full_path: str = f"{path}/{username}.json" if not path.endswith("/") else f"{path}{username}.json"

            # Save data online
            if is_online():
                response_code = self.db.write_data(full_path, encrypted_data, message=f"Saved data for {username}")
                if response_code in (200, 201):
                    if __config__.show_logs: cPrint("GREEN", f"Successfully saved online data for {username}.")
                    self.save_offline_account(username, player_instance, attributes)
                else:
                    if __config__.show_logs: cPrint("RED", f"Error saving online data for {username}. HTTP Status: {response_code}")
            else:
                if __config__.show_logs: cPrint("YELLOW", "Network is offline, saving to offline backup version.")
                if __config__.use_offline:
                    self.save_offline_account(username, player_instance, attributes)
        except Exception as e:
            if __config__.show_logs: cPrint("RED", f"Error: {e}")
            if __config__.use_offline:
                if __config__.show_logs: cPrint("GREEN", "Attempting to save to offline backup version anyway.")
                try:
                    self.save_offline_account(username, player_instance, attributes)
                except Exception as e:
                    raise Exception(f"Error: {e}")

    def save_offline_account(self, username: str, player_instance: Any, attributes: Optional[List[str]] = None) -> None:
        """
        Save full player instance to a local backup using jsonpickle.

        Args:
            username (str): The player's username.
            player_instance (Any): The player instance to save.
            attributes (Optional[List[str]]): Ignored for full object serialization.
        """
        if __config__.use_offline:
            if not os.path.exists(f"{__config__.datpath}/players"):
                os.makedirs(f"{__config__.datpath}/players")

            # Serialize full object using jsonpickle
            serialized_data: str = jsonpickle.encode(player_instance)

            # Encrypt if needed
            encrypted_data: bytes = self.encrypt_data(serialized_data)
            offline_path: str = os.path.join(f"{__config__.datpath}/players", f"{username}.gitbase")

            try:
                with open(offline_path, "wb") as file:
                    file.write(encrypted_data)
                if __config__.show_logs: cPrint("GREEN", f"Successfully saved full offline backup for {username}.")
            except Exception as e:
                raise Exception(f"Error saving full offline data: {e}")

    def load_account(self, username: str, player_instance: Any, encryption: bool) -> None:
        """
        Load a player's account data from the database or local backup.

        Args:
            username (str): The player's username.
            player_instance (Any): The player instance to populate with data.
            encryption (bool): Whether to decrypt the data.
        """
        
        try:
            path: str = f"players/{username}.json"
            offline_path: str = f"{__config__.datpath}/players/{username}.gitbase"

            if is_online():
                online_data, _ = self.db.read_data(path)
                offline_data_exists = os.path.exists(offline_path)

                if online_data:
                    # Compare timestamps to determine which data to use
                    online_timestamp = self.db.get_file_last_modified(path)
                    offline_timestamp = os.path.getmtime(offline_path) if offline_data_exists else 0

                    if offline_data_exists and offline_timestamp > online_timestamp and __config__.use_offline:
                        if __config__.show_logs: cPrint("GREEN", f"Loading offline backup for {username} (newer version found).")
                        self.use_offline_account(username, player_instance)
                        self.db.write_data(path, json.dumps(player_instance.__dict__), "Syncing offline with online")
                    else:
                        if __config__.show_logs: cPrint("GREEN", f"Loading online data for {username} (newer version).")
                        if encryption:
                            decrypted_data: str = self.decrypt_data(online_data.encode('utf-8'))
                        else:
                            decrypted_data: str = online_data
                        player_data = jsonpickle.decode(decrypted_data)
                        # Ensure we're working with an actual object or dict
                        if hasattr(player_data, '__dict__'):
                            player_instance.__dict__.update(player_data.__dict__)
                        elif isinstance(player_data, dict):
                            player_instance.__dict__.update(player_data)
                        else:
                            raise TypeError(f"Unexpected type for decoded data: {type(player_data)}")
                elif offline_data_exists and __config__.use_offline:
                    if __config__.show_logs: cPrint("GREEN", f"Loading offline backup for {username} (no online data available).")
                    self.use_offline_account(username, player_instance)
                else:
                    if __config__.show_logs: cPrint("RED", f"No data found for {username}.")
            else:
                if __config__.use_offline:
                    if __config__.show_logs: cPrint("YELLOW", "Network is offline, loading from offline backup.")
                    self.use_offline_account(username, player_instance)
        except Exception as e:
            raise Exception(f"Error loading player data: {e}")

    def use_offline_account(self, username: str, player_instance: Any) -> None:
        """
        Load a player's account data from a local backup.

        Args:
            username (str): The player's username.
            player_instance (Any): The player instance to populate with data.
        """
        if __config__.use_offline:
            
            offline_path: str = os.path.join(f"{__config__.datpath}/players", f"{username}.gitbase")

            try:
                if os.path.exists(offline_path):
                    with open(offline_path, "rb") as file:
                        encrypted_data = file.read()
                    decrypted_data: str = self.decrypt_data(encrypted_data)
                    player_data: Dict[str, Union[str, int, float]] = json.loads(decrypted_data)
                    for var, value in player_data.items():
                        setattr(player_instance, var, value)
                    if __config__.show_logs: cPrint("GREEN", f"Successfully loaded offline backup for {username}.")
                else:
                    if __config__.show_logs: cPrint("RED", f"No offline backup found for {username}.")
            except Exception as e:
                raise Exception(f"Error loading offline backup: {e}")

    def delete_account(self, username: str, delete_offline: bool = False) -> None:
        """
        Delete a player's account data from the database and optionally from local storage.

        Args:
            username (str): The player's username.
            delete_offline (bool): Whether to delete the local backup; defaults to False.
        """
        
        online_path: str = f"players/{username}.json"
        offline_path: str = os.path.join(f"{__config__.datpath}/players", f"{username}.gitbase")

        try:
            response_code = self.db.delete_data(online_path, message=f"Deleted account for {username}")
            if response_code == 204 or response_code == 200:
                if __config__.show_logs: cPrint("GREEN", f"Successfully deleted online account for {username}.")
            elif response_code == 404:
                if __config__.show_logs: cPrint("RED", f"No online account found for {username}.")
            else:
                if __config__.show_logs: cPrint("RED", f"Error deleting online account. HTTP Status: {response_code}")
        except Exception as e:
            raise Exception(f"Error deleting online account: {e}")

        if delete_offline and os.path.exists(offline_path) and __config__.use_offline:
            try:
                os.remove(offline_path)
                if __config__.show_logs: cPrint("GREEN", f"Successfully deleted offline backup for {username}.")
            except Exception as e:
                raise Exception(f"Error deleting offline backup: {e}")

    def get_all(self, path: str = "players") -> Dict[str, Any]:
        """Retrieve all player accounts stored in the system."""
        
        all_players = {}

        if is_online():
            try:
                # List all player files in the GitHub repository
                url = self.db._get_file_url(path)
                response = requests.get(url, headers=self.db.headers)

                if response.status_code == 200:
                    files = response.json()

                    if not files:
                        if __config__.show_logs: cPrint("YELLOW", "No player files found in the online repository.")
                    
                    for file in files:
                        # Process only JSON files
                        if file.get('name', '').endswith('.json'):
                            # Construct the full file path as used when saving
                            file_path = f"{path}/{file['name']}"
                            online_data, _ = self.db.read_data(file_path)

                            if online_data:
                                username = file['name'].rsplit('.', 1)[0]  # Remove '.json'
                                try:
                                    # Attempt decryption (assumes data is encrypted)
                                    decrypted_content = self.decrypt_data(online_data.encode('utf-8'))
                                except Exception as e:
                                    if __config__.show_logs: cPrint("YELLOW", f"Decryption failed for {username}, falling back to plain text: {e}")
                                    # Fallback if decryption fails (data might be plain JSON)
                                    decrypted_content = online_data
                                try:
                                    player_data = jsonpickle.decode(decrypted_content)
                                    all_players[username] = player_data
                                except json.JSONDecodeError as e:
                                    if __config__.show_logs: cPrint("RED", f"Failed to parse JSON for {username}: {e}")
                else:
                    if __config__.show_logs: cPrint("RED", f"Error retrieving player files from online database. HTTP Status: {response.status_code}")
            except Exception as e:
                if __config__.show_logs: cPrint("RED", f"Error retrieving online player data: {e}")
        else:
            if __config__.use_offline:
                if __config__.show_logs: cPrint("YELLOW", "Network is offline, loading player data from local storage.")
                offline_dir = os.path.join(__config__.datpath, path)
                if os.path.exists(offline_dir):
                    for filename in os.listdir(offline_dir):
                        if filename.endswith('.gitbase'):
                            username = filename.rsplit('.', 1)[0]  # Remove '.gitbase'
                            offline_file = os.path.join(offline_dir, filename)
                            try:
                                with open(offline_file, "rb") as f:
                                    encrypted_data = f.read()
                                try:
                                    decrypted_content = self.decrypt_data(encrypted_data)
                                except Exception as e:
                                    if __config__.show_logs: cPrint("YELLOW", f"Decryption failed for {username} offline data, falling back to plain text: {e}")
                                    # Fallback if decryption fails
                                    decrypted_content = encrypted_data.decode('utf-8')
                                player_data = jsonpickle.decode(decrypted_content)
                                all_players[username] = player_data
                            except Exception as e:
                                if __config__.show_logs: cPrint("RED", f"Error loading offline data for {username}: {e}")
                else:
                    if __config__.show_logs: cPrint("YELLOW", f"Offline directory {offline_dir} does not exist.")

        if not all_players:
            if __config__.show_logs: cPrint("YELLOW", "No players found in either online or offline storage.")
        
        return all_players