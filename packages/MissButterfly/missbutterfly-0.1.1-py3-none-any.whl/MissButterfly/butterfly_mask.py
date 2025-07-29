"""
butterfly_mask.py
=================

Provides the ButterflyMask class for reversible string obfuscation using Caesar cipher and deterministic shuffling.

:author: Sundram
:organization: FireIndex
:copyright: (c) 2025 FireIndex
:license: MIT, see LICENSE for more details.
"""

from typing import Literal, Dict, Any
from .string_shuffler import StringShuffler
from .caesar_cipher import CaesarCipher

__all__ = ["ButterflyMask"]


class ButterflyMask:
    """
    ButterflyMask provides reversible string obfuscation using a combination of
    Caesar cipher and deterministic shuffling.

    This class allows you to encode and decode strings using a two-layer process:
    - First, a Caesar cipher is applied (with a configurable shift).
    - Second, the result is shuffled deterministically using a salt and optional randomization.

    Example:
        >>> mask = ButterflyMask(salt="mysalt", shifte=5, shuffle_mode="mixed")
        >>> encoded = mask.encode("SensitiveData123")
        >>> decoded = mask.decode(encoded)
        >>> print(decoded)
        SensitiveData123

    Args:
        salt (str): Salt value for deterministic shuffling.
        shifte (int): Shift value for the outer Caesar cipher.
        shuffle_mode (Literal['mixed', 'fixed']): Shuffle mode, either 'mixed' (randomized) or 'fixed' (deterministic).
    """

    __slots__ = ("salt", "shifte", "shuffle_mode", "user_cipher")

    def __init__(
        self,
        salt: str = "InitialSaltValue",
        shifte: int = 3,
        shuffle_mode: Literal['mixed', 'fixed'] = 'mixed'
    ) -> None:
        self._validate_salt(salt)
        self._validate_shuffle_mode(shuffle_mode)
        self.salt = salt
        self.shifte = shifte
        self.shuffle_mode = shuffle_mode
        self.user_cipher = CaesarCipher(shift=self.shifte)

    @staticmethod
    def _validate_salt(salt: str) -> None:
        if not isinstance(salt, str):
            raise TypeError("salt must be a string.")

    @staticmethod
    def _validate_shuffle_mode(mode: str) -> None:
        if mode not in ('mixed', 'fixed'):
            raise ValueError("shuffle_mode must be 'mixed' or 'fixed'.")

    def encode(self, s: str) -> str:
        """
        Encode a string using Caesar cipher and deterministic shuffling.

        Args:
            s (str): The string to encode.
        Returns:
            str: The encoded string.
        Raises:
            TypeError: If input is not a string.
        """
        import random

        if not isinstance(s, str):
            raise TypeError("Input must be a string.")
        if not s:
            return ""

        shuffle_round = (
            str(random.randint(0, 9999)).rjust(4, '0')
            if self.shuffle_mode == 'mixed' else ""
        )
        salted = self.salt + shuffle_round
        shift_value = int(shuffle_round) if shuffle_round else 3

        shifted = CaesarCipher(shift=shift_value).encrypt(s)
        shuffler = StringShuffler(salt=salted)
        shuffled = shuffler.shuffle(shifted)
        encoded = f"{shuffled}_{shuffle_round}" if shuffle_round else shuffled
        encoded = self.user_cipher.encrypt(encoded)
        return encoded

    def decode(self, s: str) -> str:
        """
        Decode a string previously encoded by this shuffler.

        Args:
            s (str): The encoded string.
        Returns:
            str: The original string.
        Raises:
            TypeError: If input is not a string.
            ValueError: If the encoded string format is invalid.
        """
        if not isinstance(s, str):
            raise TypeError("Encoded string must be a string.")
        
        if not s:
            return ""

        decoded = self.user_cipher.decrypt(s)

        shuffled, shuffle_round = decoded, ""
        if self.shuffle_mode != 'fixed':
            if '_' not in decoded:
                raise ValueError("Encoded string format invalid: missing shuffle_round.")
            shuffled, shuffle_round = decoded.rsplit('_', 1)
        if not shuffled:
            raise ValueError("Encoded string format invalid: empty shuffled part.")

        if shuffle_round and (not shuffle_round.isdigit() or len(shuffle_round) != 4):
            raise ValueError("Encoded string format invalid: bad shuffle_round.")

        salted = self.salt + shuffle_round
        shuffler = StringShuffler(salt=salted)
        shifted = shuffler.unshuffle(shuffled)
        shift_value = int(shuffle_round) if shuffle_round else 3
        original = CaesarCipher(shift=shift_value).decrypt(shifted)
        return original

    def dict(self) -> Dict[str, Any]:
        """
        Return the configuration as a dictionary.

        Returns:
            Dict[str, Any]: The configuration dictionary.
        """
        return {
            "salt": self.salt,
            "shifte": self.shifte,
            "shuffle_mode": self.shuffle_mode
        }

    def copy(self, **kwargs: Any) -> "ButterflyMask":
        """
        Return a copy of this shuffler, optionally overriding parameters.

        Args:
            **kwargs: Parameters to override.
        Returns:
            ButterflyMask: The copied shuffler.
        """
        data = self.dict()
        data.update(kwargs)
        return ButterflyMask(**data)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"salt={self.salt!r}, "
            f"shifte={self.shifte!r}, "
            f"shuffle_mode={self.shuffle_mode!r})"
        )
