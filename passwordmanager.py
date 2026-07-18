"""
storage.py
----------
Purpose:
    Handle all reading and writing of the vault file on disk, including
    encryption and decryption of the stored credentials.

Why this file exists:
    Separating storage from business logic (password_manager.py) and from
    authentication (auth.py) means the on-disk file format, encryption
    scheme, or storage backend (JSON today, SQLite tomorrow) can change
    without touching the rest of the application. This follows the
    Single Responsibility Principle and makes the codebase easier to test
    and maintain.

Security note:
    Credentials are never written to disk in plain text. The entire vault
    (the list of credential records) is serialized to JSON, then encrypted
    as a single blob using a Fernet key that is derived from the user's
    master password (see auth.py). Only the encrypted blob and a random
    salt are stored in data.json -- never the master password itself.
"""

import json
import os
from typing import Any, Dict, List

from cryptography.fernet import Fernet


class Storage:
    """
    Responsible for persisting the encrypted vault to a JSON file and
    loading it back into memory.
    """

    def __init__(self, file_path: str = "data.json") -> None:
        self.file_path = file_path

    def file_exists(self) -> bool:
        """Return True if a vault file already exists on disk."""
        return os.path.exists(self.file_path)

    def read_raw(self) -> Dict[str, Any]:
        """
        Read the raw (still-encrypted) contents of the vault file.

        Returns:
            A dict with keys "salt" and "vault" (both base64 strings).

        Raises:
            FileNotFoundError: If no vault file exists yet.
            ValueError: If the file exists but is not valid JSON, which
                would indicate a corrupted or tampered file.
        """
        if not self.file_exists():
            raise FileNotFoundError(f"No vault file found at '{self.file_path}'.")

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Vault file '{self.file_path}' is corrupted or not valid JSON."
            ) from error

    def write_raw(self, salt: str, encrypted_vault: str) -> None:
        """
        Write the salt and encrypted vault blob to disk as JSON.

        Args:
            salt: Base64-encoded random salt used for key derivation.
            encrypted_vault: The Fernet-encrypted, base64-encoded vault.

        Why it's a single combined write:
            Writing both fields together (rather than separate files)
            keeps the vault atomic and simple to back up or move.
        """
        data = {"salt": salt, "vault": encrypted_vault}
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def load_vault(self, key: bytes) -> List[Dict[str, str]]:
        """
        Decrypt and return the list of credential records.

        Args:
            key: The Fernet encryption key derived from the master password.

        Returns:
            A list of credential dictionaries. An empty list if the vault
            has just been created and has no encrypted data yet.

        Raises:
            InvalidToken: If the key is wrong (i.e. incorrect master
                password) -- this is how login verification works, see
                auth.py for details.
        """
        raw = self.read_raw()
        encrypted_vault = raw.get("vault", "")

        if not encrypted_vault:
            return []

        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(encrypted_vault.encode("utf-8"))
        return json.loads(decrypted_bytes.decode("utf-8"))

    def save_vault(self, key: bytes, salt: str, credentials: List[Dict[str, str]]) -> None:
        """
        Encrypt the given credential list and persist it to disk.

        Args:
            key: The Fernet encryption key derived from the master password.
            salt: The salt to store alongside the encrypted data (needed
                to re-derive the same key on the next login).
            credentials: The current in-memory list of credential records.

        Why it exists:
            Called after every add/edit/delete operation so the on-disk
            vault always reflects the latest in-memory state
            ("auto-save"), satisfying the requirement that changes persist
            immediately rather than requiring an explicit "save" action.
        """
        fernet = Fernet(key)
        plaintext_bytes = json.dumps(credentials).encode("utf-8")
        encrypted_bytes = fernet.encrypt(plaintext_bytes)
        self.write_raw(salt, encrypted_bytes.decode("utf-8"))