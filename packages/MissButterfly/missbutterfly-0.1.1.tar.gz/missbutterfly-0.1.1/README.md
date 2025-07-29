# MissButterfly

**MissButterfly** is a Python package for reversible string obfuscation, combining deterministic shuffling (using a salt) and Caesar cipher shifting. It is designed for lightweight, fast, and practical masking of sensitive data in logs, URLs, or configuration files.

> **Why the name "MissButterfly"?**
> There is no technical reason for this name. I am a huge fan of animated series, and one of my favorites is "Star vs. the Forces of Evil." The main character, Star Butterfly, inspired the name of this project. She is one of my favorite characters in the series, along with Marco and Hekapoo. This project is named in her honor.

> **Note:**  
> The core module `butterfly_encoding` is planned for future releases.  
> Currently, the main feature is the robust `ButterflyMask` class, which provides strong, layered obfuscation.

---

## Why MissButterfly?

- **Layered Obfuscation:** Combines deterministic, salt-based shuffling and Caesar cipher shifting for robust, reversible masking.
- **Difficult to Crack:** For large strings, the combination of seeded shuffling and shifting makes brute-force reversal extremely difficult without the correct parameters.
- **Reversible:** Unlike hashing, you can always recover the original string if you know the salt and parameters.
- **Lightweight & Dependency-Free:** Pure Python, no external dependencies, Python 3.7+ compatible.

---

## Features

- **ButterflyMask:**
  - Reversible, layered obfuscation using both Caesar cipher and deterministic shuffling.
  - Configurable salt, shuffle mode (`fixed` or `mixed`), and Caesar shift.
  - Suitable for masking sensitive data in logs, URLs, or configs.
- **StringShuffler:**
  - Deterministic, salt-based string shuffling and unshuffling.
- **CaesarCipher:**
  - Classic Caesar cipher for simple character shifting.

---

## ButterflyMask Shuffle Modes: `fixed` vs `mixed`

- **fixed:**  
  The encoding output of a given string will always be the same for the same salt and shift.

  > _Example: Encoding "Hello" with the same salt and shift will always produce the same encoded string._

- **mixed:**  
  The encoding output of a given string may be different each time you encode, even with the same salt and shift.  
  However, **every encoded string can always be decoded back to the original string**.
  > _Example: Encoding "Hello" multiple times may produce different encoded strings, but all will decode to "Hello"._

---

## Installation

```bash
pip install MissButterfly
```

Or, from source:

```bash
git clone https://github.com/FireIndex/MissButterfly.git
cd MissButterfly
pip install .
```

---

## Usage

### ButterflyMask: Powerful, Reversible Masking

```python
from MissButterfly import ButterflyMask

original = "SensitiveData123"

# Mixed shuffle mode (randomized per encode)
mask = ButterflyMask(salt="mysalt", shuffle_mode="mixed")
encoded = mask.encode(original) # Output may varry, ex. ne3tvai1eaSi2sDt_2129
print(f"Encoded: {encoded}")
decoded = mask.decode(encoded)
print(f"Decoded: {decoded}")  # Output: SensitiveData123

# Fixed shuffle mode (deterministic)
mask = ButterflyMask(salt="mysalt", shuffle_mode="fixed")
encoded = mask.encode(original) # Output: 3botzg1ko2kygYzJ
print(f"Encoded (fixed): {encoded}")
decoded = mask.decode(encoded)
print(f"Decoded (fixed): {decoded}")
```

#### Custom Caesar Cipher Shift

```python
mask = ButterflyMask(salt="mysalt", shifte=7, shuffle_mode="mixed")
encoded = mask.encode("MySecret")
decoded = mask.decode(encoded)
```

---

### CaesarCipher: Classic Shifting

```python
from MissButterfly import CaesarCipher

cipher = CaesarCipher(shift=5)
encrypted = cipher.encrypt("HelloWorld")  # Output: MjqqtBtwqi
decrypted = cipher.decrypt(encrypted)     # Output: HelloWorld
```

---

### StringShuffler: Deterministic Shuffling

```python
from MissButterfly import StringShuffler

shuffler = StringShuffler(salt="mysalt")
shuffled = shuffler.shuffle("HelloWorld")
unshuffled = shuffler.unshuffle(shuffled)
print(unshuffled)  # Output: HelloWorld
```

---

## API Reference

### ButterflyMask

```python
ButterflyMask(
    salt: str = "InitialSaltValue",
    shifte: int = 3,
    shuffle_mode: Literal['mixed', 'fixed'] = 'mixed'
)
```

- `salt`: Salt value for deterministic shuffling.
- `shifte`: Shift value for the outer Caesar cipher.
- `shuffle_mode`: `'mixed'` (random shuffle per encode) or `'fixed'` (deterministic).

**Methods:**

- `encode(s: str) -> str`: Encode a string.
- `decode(s: str) -> str`: Decode a previously encoded string.
- `dict() -> dict`: Get configuration as a dictionary.
- `copy(**kwargs) -> ButterflyMask`: Copy with optional overrides.

### CaesarCipher

```python
CaesarCipher(shift: int)
```

- `encrypt(text: str) -> str`
- `decrypt(text: str) -> str`

### StringShuffler

```python
StringShuffler(salt: str)
```

- `shuffle(s: str) -> str`
- `unshuffle(shuffled_str: str) -> str`

---

## Roadmap

- **butterfly_encoding:**  
  The upcoming core module for even more advanced, flexible, and secure encoding/decoding.

---

## License

MIT License

---

**Disclaimer:**  
MissButterfly is intended for lightweight obfuscation and masking, not for strong cryptographic security. Do not use for protecting highly sensitive or regulated data.
