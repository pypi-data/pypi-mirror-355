"""
GVOTP - A lightweight in-memory OTP (One-Time Password) generator and verifier.

Author: Bittu Singh
Email: bittusinghtech@gmail.com

Description:
    GVOTP allows you to generate and verify time-bound 6-digit OTPs in memory.
    It also supports verification using externally stored OTP records, making it
    flexible for use cases involving database or cache-backed OTP storage.

Example usage:
    >>> otp_manager = GVOTP()
    >>> result = otp_manager.generate_otp("email", "user@example.com")
    >>> otp = result["otp"]
    >>> otp_manager.verify_otp("email", "user@example.com", otp)

    # For external storage:
    >>> stored_record = result["otp_record"]
    >>> otp_manager.verify_otp("email", "user@example.com", otp, document=stored_record)
"""

import hashlib
import hmac
import time
import secrets
from typing import Optional, Dict


class OTPError(Exception):
    """Base exception for OTP errors."""


class OTPNotFound(OTPError):
    """Raised when the OTP record is not found."""


class OTPExpired(OTPError):
    """Raised when the OTP has expired."""


class OTPTooManyAttempts(OTPError):
    """Raised when the OTP has been tried too many times."""


class OTPInvalid(OTPError):
    """Raised when the OTP is incorrect."""


class GVOTP:
    """GVOTP - In-memory OTP generation and verification class."""

    def __init__(self):
        self._store: Dict[str, Dict] = {}

    @staticmethod
    def _hash_otp(otp: str) -> str:
        """Return SHA256 hash of the OTP."""
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def _key(kind: str, receiver: str) -> str:
        """Generate a unique key based on kind and receiver."""
        return f"{kind}:{receiver.lower() if kind == 'email' else receiver}"

    def generate_otp(self, kind: str, receiver: str, ttl: int = 900) -> Dict[str, object]:
        """
        Generate a 6-digit OTP for the given identifier.

        Args:
            kind (str): Type of identifier (e.g., "email", "phone").
            receiver (str): Identifier receiver (e.g., email address).
            ttl (int): Time-to-live in seconds (default: 900).

        Returns:
            dict: OTP, record, and storage key.
        """
        otp = str(secrets.randbelow(1000000)).zfill(6)
        otp_hash = self._hash_otp(otp)
        now = int(time.time())
        key = self._key(kind, receiver)

        # Preserve attempts on regeneration
        existing_record = self._store.get(key, {})
        attempts = existing_record.get("attempts", 0)

        record = {
            "kind": kind,
            "receiver": receiver.lower() if kind == "email" else receiver,
            "otp_hash": otp_hash,
            "attempts": attempts,
            "create_time": now,
            "ttl": ttl
        }

        self._store[key] = record

        return {
            "otp": otp,
            "otp_record": record
        }

    def verify_otp(self, kind: str, receiver: str, otp: str, document: Optional[Dict] = None) -> bool:
        """
        Verify the provided OTP.

        Args:
            kind (str): Identifier type.
            receiver (str): Identifier receiver.
            otp (str): OTP entered by user.
            document (dict, optional): External OTP record, if not using in-memory.

        Raises:
            OTPNotFound: If no OTP record is found.
            OTPExpired: If the OTP has expired.
            OTPTooManyAttempts: If maximum retries are exceeded.
            OTPInvalid: If the OTP is incorrect.

        Returns:
            bool: True if OTP is valid.
        """
        key = self._key(kind, receiver)
        record = document or self._store.get(key)

        if not record:
            raise OTPNotFound("OTP not found.")

        now = int(time.time())
        if now - record["create_time"] > record["ttl"]:
            if document is None:
                self._store.pop(key, None)
            raise OTPExpired("OTP expired.")

        if record["attempts"] >= 5:
            raise OTPTooManyAttempts("Too many failed attempts.")

        if not hmac.compare_digest(self._hash_otp(otp), record["otp_hash"]):
            if document is None:
                record["attempts"] += 1
                self._store[key] = record
            raise OTPInvalid("Invalid OTP.")

        if document is None:
            self._store.pop(key, None)

        return True
