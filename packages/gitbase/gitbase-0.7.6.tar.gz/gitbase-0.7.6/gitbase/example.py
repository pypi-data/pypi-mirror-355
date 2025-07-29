# GitBase v0.7.6 Showcase Example

from gitbase import MultiBase, PlayerDataSystem, DataSystem, NotificationManager, ProxyFile, __config__, is_online
from cryptography.fernet import Fernet
import sys

# -------------------------
# Online Status Check
# -------------------------
print(f"Is Online: {is_online()}")  # Check if the system is online

# -------------------------
# GitHub Database Setup
# -------------------------
encryption_key = Fernet.generate_key()  # Generate encryption key for secure storage

# MultiBase setup with fallback repository configurations (if needed)
database = MultiBase([
    {
        "token": "YOUR_TOKEN",
        "repo_owner": "YOUR_GITHUB_USERNAME",
        "repo_name": "YOUR_REPO_NAME",
        "branch": "main"
    },
    # Additional GitBase configurations can be added here
    # {"token": "SECOND_TOKEN", "repo_owner": "SECOND_USERNAME", "repo_name": "SECOND_REPO", "branch": "main"}
])
# When using Legacy GitBase do the below instead (will be a single repository)
# from gitbase import GitBase
# database = GitBase(token=GITHUB_TOKEN, repo_owner=REPO_OWNER, repo_name=REPO_NAME)

# -------------------------
# Configure GitBase
# -------------------------

__config__.app_name = "Cool RPG Game"
__config__.publisher = "Taireru LLC"
__config__.version = "1.0.0"
__config__.use_offline = True # defaults to `True`, no need to type out unless you want to set it to `False`
__config__.show_logs = True # defaults to `True`, no need to type out unless you want to set it to `False`
__config__.use_version_path = False # defaults to `True`, this variable will decide if your app path will use a version subdirectory (meaning different versions will have different data)
__config__.setdatpath() # Update `datpath` variable of `__config__` for offline data saving (you can also set it manually via `__config__.datpath = 'path/to/data'`)
# the path setup with `__config__.cleanpath` property can be used for other application needs besides GitBase, it will return a clean path based on your os (ex. Windows -> C:/Users/YourUsername/Documents/Taireru LLC/Cool RPG Game/)

# -------------------------
# System Instantiation
# -------------------------
player_data_system = PlayerDataSystem(db=database, encryption_key=encryption_key)
data_system = DataSystem(db=database, encryption_key=encryption_key)

# -------------------------
# Player Class Definition
# -------------------------
class Player:
    def __init__(self, username, score, password):
        self.username = username
        self.score = score
        self.password = password

# Create a sample player instance
player = Player(username="john_doe", score=100, password="123")

# -------------------------
# Save & Load Player Data with Encryption
# -------------------------
# Save player data to the repository (with encryption)
player_data_system.save_account(
    username="john_doe",
    player_instance=player,
    encryption=True,
    attributes=["username", "score", "password"],
    path="players"
)

# Load player data
player_data_system.load_account(username="john_doe", player_instance=player, encryption=True)

# -------------------------
# Game Flow Functions
# -------------------------
def load_game():
    print("Game starting...")

def main_menu():
    sys.exit("Exiting game...")

# -------------------------
# Account Validation & Login
# -------------------------
# Validate player credentials
if player_data_system.get_all(path="players"):
    if player.password == input("Enter your password: "):
        print("Login successful!")
        load_game()
    else:
        print("Incorrect password!")
        main_menu()

# -------------------------
# Save & Load General Data with Encryption
# -------------------------
# Save data (key-value) to the repository (with encryption)
data_system.save_data(key="key_name", value=69, path="data", encryption=True)

# Load and display specific key-value pair
loaded_key_value = data_system.load_data(key="key_name", path="data", encryption=True)
print(f"Key: {loaded_key_value.key}, Value: {loaded_key_value.value}")

# Display all stored data
print("All stored data:", data_system.get_all(encryption=True, path="data"))

# Delete specific key-value data
data_system.delete_data(key="key_name", path="data")

# -------------------------
# Player Account Management
# -------------------------
# Display all player accounts
print("All player accounts:", player_data_system.get_all(path="players"))

# Delete a specific player account
NotificationManager.hide()  # Hide notifications temporarily
player_data_system.delete_account(username="john_doe")
NotificationManager.show()  # Show notifications again