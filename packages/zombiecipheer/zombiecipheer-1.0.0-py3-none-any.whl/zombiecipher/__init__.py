# zombie/__init__.py

class ZombieCipher:
    def __init__(self, key: bytes):
        if not key:
            raise ValueError("Key cannot be empty.")
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        return bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(data)])

    def decrypt(self, data: bytes) -> bytes:
        return self.encrypt(data)

    def to_hex(self, data: bytes) -> str:
        return ''.join(format(b, '02x') for b in data)

    def from_hex(self, hex_str: str) -> bytes:
        if len(hex_str) % 2 != 0:
            raise ValueError("Invalid HEX string length")
        return bytes(int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2))
