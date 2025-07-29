"""
caesar_cipher.py
===============

A robust and efficient Caesar cipher implementation for encrypting and decrypting text.

:author: Sundram
:organization: FireIndex
:copyright: (c) 2025 FireIndex
:license: MIT, see LICENSE for more details.
"""

from typing import Any

__all__ = ["CaesarCipher"]

class CaesarCipher:
    """
    CaesarCipher provides methods to encrypt and decrypt text using the classic Caesar cipher.

    Example:
        >>> cipher = CaesarCipher(shift=3)
        >>> cipher.encrypt("Hello, World!")
        'Khoor, Zruog!'
        >>> cipher.decrypt("Khoor, Zruog!")
        'Hello, World!'
    """

    def __init__(self, shift: int) -> None:
        """
        Initialize the CaesarCipher with a shift value.

        Args:
            shift (int): The shift value for the cipher.
        Raises:
            TypeError: If shift is not an integer.
        """
        if not isinstance(shift, int):
            raise TypeError("shift must be an integer")
        self.shift = shift

    def encrypt(self, text: str) -> str:
        """
        Encrypt the text using the Caesar cipher.

        Args:
            text (str): The text to encrypt.
        Returns:
            str: The encrypted text.
        Raises:
            TypeError: If text is not a string.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return self._shift_text(text, self.shift)

    def decrypt(self, text: str) -> str:
        """
        Decrypt the text using the Caesar cipher.

        Args:
            text (str): The text to decrypt.
        Returns:
            str: The decrypted text.
        Raises:
            TypeError: If text is not a string.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return self._shift_text(text, -self.shift)

    @staticmethod
    def _shift_text(text: str, shift: int) -> str:
        """
        Shift the text by the given amount, preserving case and non-alphabetic characters.

        Args:
            text (str): The text to shift.
            shift (int): The shift amount.
        Returns:
            str: The shifted text.
        """
        result = []
        for char in text:
            if char.isupper():
                base = ord('A')
                shifted = (ord(char) - base + shift) % 26 + base
                result.append(chr(shifted))
            elif char.islower():
                base = ord('a')
                shifted = (ord(char) - base + shift) % 26 + base
                result.append(chr(shifted))
            else:
                result.append(char)
        return ''.join(result)