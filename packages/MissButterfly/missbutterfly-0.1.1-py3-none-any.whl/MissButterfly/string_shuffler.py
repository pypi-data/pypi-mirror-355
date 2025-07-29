"""
string_shuffler.py
=================

A robust, deterministic string shuffler for reversible obfuscation using a salt.

:author: Sundram
:organization: FireIndex
:copyright: (c) 2025 FireIndex
:license: MIT, see LICENSE for more details.
"""

import random
from typing import List

__all__ = ["StringShuffler"]

class StringShuffler:
    """
    StringShuffler provides deterministic string shuffling and unshuffling using a salt value.

    Example:
        >>> shuffler = StringShuffler(salt="mysalt")
        >>> shuffled = shuffler.shuffle("HelloWorld")
        >>> original = shuffler.unshuffle(shuffled)
        >>> print(original)
        HelloWorld
    """

    def __init__(self, salt: str) -> None:
        """
        Initialize the StringShuffler with a salt.

        Args:
            salt (str): The salt value to seed the shuffling.
        Raises:
            TypeError: If salt is not a string.
        """
        if not isinstance(salt, str):
            raise TypeError("salt must be a string")
        self.salt = salt

    def _get_indices(self, length: int) -> List[int]:
        """
        Generate a shuffled list of indices based on the salt.

        Args:
            length (int): The length of the string to shuffle.
        Returns:
            List[int]: A list of shuffled indices.
        """
        rnd = random.Random(self.salt)
        indices = list(range(length))
        rnd.shuffle(indices)
        return indices

    def shuffle(self, s: str) -> str:
        """
        Shuffle the characters in the string deterministically.

        Args:
            s (str): The string to shuffle.
        Returns:
            str: The shuffled string.
        Raises:
            TypeError: If s is not a string.
        """
        if not isinstance(s, str):
            raise TypeError("s must be a string")
        indices = self._get_indices(len(s))
        shuffled = [''] * len(s)
        for i, idx in enumerate(indices):
            shuffled[idx] = s[i]
        return ''.join(shuffled)

    def unshuffle(self, shuffled_str: str) -> str:
        """
        Reverse the shuffling process to retrieve the original string.

        Args:
            shuffled_str (str): The shuffled string.
        Returns:
            str: The original unshuffled string.
        Raises:
            TypeError: If shuffled_str is not a string.
        """
        if not isinstance(shuffled_str, str):
            raise TypeError("shuffled_str must be a string")
        indices = self._get_indices(len(shuffled_str))
        original = [''] * len(shuffled_str)
        for i, idx in enumerate(indices):
            original[i] = shuffled_str[idx]
        return ''.join(original)
