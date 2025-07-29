import requests
import json
import os
import math
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
from altcolor import cPrint
from .gitbase import GitBase, is_online
from moviepy.video.io.VideoFileClip import VideoFileClip  # Video handling
from .config import canUse
from .__config__ import config as __config__
from .multibase import MultiBase
from typing import Union, Any, Optional
import jsonpickle

class KeyValue:
    """
    Represents a key-value pair for storing data.
    
    Attributes:
        key (str): The key to represent the pair.
        value (Any): The value connected to the key. Can be anything.
    """

    def __init__(self, key: str, value: Any) -> None:
        self.key: str = key
        self.value: Any = value

def is_probably_encrypted(data: str) -> bool:
    try:
        # Fernet-encrypted strings are Base64-encoded, 128+ chars, no curly braces
        return not data.strip().startswith("{")
    except:
        return True

class DataSystem:
    """
    Handles data storage and retrieval, supporting online GitBase and offline backups.
    """

    def __init__(self, db: Union[GitBase, MultiBase], encryption_key: bytes) -> None:
        """
        Initializes the DataSystem with a GitBase instance and encryption key.

        Args:
            db (GitBase): The GitBase instance for online storage.
            encryption_key (bytes): The key used for encryption.
        """
        self.db: Union[GitBase, MultiBase] = db
        self.encryption_key: bytes = encryption_key
        self.fernet: Fernet = Fernet(self.encryption_key)

    def encrypt_data(self, data: str) -> bytes:
        """
        Encrypts the given data.

        Args:
            data (str): The data to encrypt.

        Returns:
            bytes: The encrypted data.
        """
        return self.fernet.encrypt(data.encode('utf-8'))

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Decrypts the given encrypted data.

        Args:
            encrypted_data (bytes): The data to decrypt.

        Returns:
            str: The decrypted data.
        """
        return self.fernet.decrypt(encrypted_data).decode('utf-8')

    def save_data(self, key: str, value: Any, path: str = "data", encryption: bool = False) -> None:
        """
        Saves data to online storage, or offline backup if offline.

        Args:
            key (str): The key associated with the data.
            value (Any): The data to store.
            path (str, optional): The storage path. Defaults to "data".
            encryption (bool, optional): Whether to encrypt the data. Defaults to False.
        """
        try:
            serialized_data = jsonpickle.encode(value)
            data: str = (
                self.encrypt_data(serialized_data).decode('utf-8') if encryption else serialized_data
            )
            full_path = os.path.join(path, f"{key}.json")

            if is_online():
                response_code: int = self.db.write_data(path, data, message=f"Saved {key}")
                if response_code in (200, 201):
                    if __config__.show_logs: cPrint("GREEN", f"Successfully saved online data for {key}.")
                else:
                    if __config__.show_logs: cPrint("RED", f"Error saving online data for {key}. HTTP Status: {response_code}")
            else:
                if __config__.show_logs: cPrint("YELLOW", "Network is offline, saving to offline backup version.")
                if __config__.use_offline:
                    self.use_offline_data(key, value, encryption)
        except Exception as e:
            if __config__.show_logs: cPrint("RED", f"Error: {e}")
            if __config__.show_logs: cPrint("GREEN", "Attempting to save to offline backup version anyway.")
            try:
                if __config__.use_offline:
                    self.use_offline_data(key, value, encryption)
            except Exception as e:
                raise Exception(f"Error saving to offline backup: {e}")


    def load_data(self, key: str, encryption: bool, path: str = "data") -> Optional[KeyValue]:
        """
        Loads data from online storage or offline backup.

        Args:
            key (str): The key associated with the data.
            encryption (bool): Whether the data is encrypted.
            path (str, optional): The storage path. Defaults to "data".

        Returns:
            Optional[KeyValue]: The retrieved data or None if not found.
        """
        path = os.path.join(path, f"{key}.json")
        try:
            if is_online():
                online_data, _ = self.db.read_data(path)

                if online_data:
                    try:
                        if encryption and is_probably_encrypted(online_data):
                            decrypted_data = self.decrypt_data(online_data.encode("utf-8"))
                        else:
                            decrypted_data = online_data

                        try:
                            parsed = jsonpickle.decode(decrypted_data)
                            return KeyValue(key, parsed)
                        except Exception as json_err:
                            raise Exception(f"Deserialization error for key '{key}': {json_err}")
                    except Exception as decrypt_err:
                        raise Exception(f"Decryption or decoding error for key '{key}': {decrypt_err}")
                else:
                    if __config__.show_logs: cPrint("RED", f"No online data found for {key}.")
            else:
                if __config__.show_logs: cPrint("YELLOW", "Network is offline, loading from offline backup.")
                if __config__.use_offline:
                    return self.use_offline_data(key, encryption)
        except Exception as e:
            raise Exception(f"Error loading data for key '{key}': {e}")
        
    def use_offline_data(self, key: str, value: Any, enc: bool = False) -> Optional[KeyValue]:
        """
        Loads offline data from the local backup.

        Args:
            key (str): The key associated with the data.
            encryption (bool): Whether the data is encrypted.

        Returns:
            Optional[KeyValue]: The loaded key-value object, or None if not found.
        """
        if __config__.use_offline:
            path: str = os.path.join(f"{__config__.datpath}/data", f"{key}.gitbase")
            if not os.path.exists(path):
                if __config__.show_logs: cPrint("RED", f"No offline data found for key: {key}")
                return None

            try:
                with open(path, "rb") as file:
                    raw_data = file.read()
                    decoded_data = self.decrypt_data(raw_data) if enc else raw_data.decode("utf-8")
                    v = jsonpickle.decode(decoded_data) or value
                    return KeyValue(key, v)
            except Exception as e:
                raise Exception(f"Failed to load offline data for '{key}': {e}")

    def delete_data(self, key: str, path: str = "data", delete_offline: bool = False) -> None:
        """
        Deletes data from online storage and optionally offline storage.

        Args:
            key (str): The key associated with the data.
            path (str, optional): The storage path. Defaults to "data".
            delete_offline (bool, optional): Whether to delete offline storage as well. Defaults to False.
        """
        full_path = os.path.join(path, f"{key}.json")
        try:
            response_code: int = self.db.delete_data(path, message=f"Deleted {key}")
            if response_code in (200, 204):
                if __config__.show_logs: cPrint("GREEN", f"Successfully deleted online data for {key}.")
            elif response_code == 404:
                if __config__.show_logs: cPrint("RED", f"No online data found for {key}.")
            else:
                if __config__.show_logs: cPrint("RED", f"Error deleting online data for {key}. HTTP Status: {response_code}")
        except Exception as e:
            if __config__.show_logs: cPrint("RED", f"Error deleting online data: {e}")

        if delete_offline:
            offline_path: str = os.path.join(f"{__config__.datpath}/data", f"{key}.gitbase")
            if os.path.exists(offline_path):
                os.remove(offline_path)
                if __config__.show_logs: cPrint("GREEN", f"Successfully deleted offline backup for {key}.")
            else:
                if __config__.show_logs: cPrint("RED", f"No offline backup found for {key}.")

    def get_all(self, encryption: bool, path: Optional[str] = f"{__config__.datpath}/data") -> Dict[str, Any]:
        """
        Retrieves all key-value pairs stored in the system.

        Args:
            encryption (bool): Whether to decrypt the data after loading.
            path (str, optional): The directory path to retrieve data from. Defaults to "__config__.datpath/data".

        Returns:
            Dict[str, Any]: A dictionary of all key-value pairs.
        """
        all_data = {}
        if is_online():
            try:
                keys = self.db.get_all_keys(path)
                for key in keys:
                    online_data, _ = self.db.read_data(f"{path}/{key}.json")
                    if online_data:
                        value = self.load_data(key, encryption, path)
                        all_data[key] = value
            except Exception as e:
                if __config__.show_logs: cPrint("RED", f"Error loading online data: {e}")
        else:
            if __config__.use_offline:
                if __config__.show_logs: cPrint("YELLOW", "Network is offline, loading from offline backup.")
                files = os.listdir(path)
                for file in files:
                    if file.endswith(".gitbase"):
                        key = file[:-len(".gitbase")]
                        try:
                            with open(os.path.join(path, file), "rb") as f:
                                raw_data = f.read()
                                decoded_data = self.decrypt_data(raw_data) if encryption else raw_data.decode("utf-8")
                                all_data[key] = jsonpickle.decode(decoded_data)
                        except Exception as e:
                            if __config__.show_logs: cPrint("RED", f"Error loading offline data for {key}: {e}")

        return all_data

    def chunk(self, file_path: str, output_dir: str, duration_per_chunk: int = 90) -> None:
        """
        Splits a video into smaller chunks.

        Args:
            file_path (str): Path to the input video file.
            output_dir (str): Directory to save the chunks.
            duration_per_chunk (int, optional): Duration of each chunk in seconds. Defaults to 90.
        """
        os.makedirs(output_dir, exist_ok=True)
        try:
            with VideoFileClip(file_path) as video:
                total_duration: float = video.duration
                num_chunks: int = max(4, math.ceil(total_duration / duration_per_chunk))
                chunk_duration: float = total_duration / num_chunks

                for i in range(num_chunks):
                    start_time: float = i * chunk_duration
                    end_time: float = min((i + 1) * chunk_duration, total_duration)
                    chunk_path: str = os.path.join(output_dir, f"chunk_{i + 1}.mp4")
                    video.subclip(start_time, end_time).write_videofile(chunk_path, codec="libx264", audio_codec="aac")
        except Exception as e:
            raise Exception(f"Error during chunking: {e}")