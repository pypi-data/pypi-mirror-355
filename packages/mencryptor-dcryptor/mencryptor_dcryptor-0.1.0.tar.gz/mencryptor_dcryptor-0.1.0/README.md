# mencryptor-dcryptor

A Python module to encrypt and decrypt code or text using custom character-to-number mapping.

## Installation
```bash
pip install mencryptor-dcryptor
```

## Usage
```python
from mencryptor_dcryptor import encrypt, decrypt

text = "def add(a, b): return a + b"
encrypted = encrypt(text)
print(encrypted)

decrypted = decrypt(encrypted)
print(decrypted)
```
