from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass


@dataclass(slots=True)
class BloomFilter:
    """Simplified Bloom filter for teaching use."""

    bits: int
    num_hashes: int
    bit_array: bytearray

    @classmethod
    def create(cls, bits: int, num_hashes: int = 3) -> "BloomFilter":
        if bits <= 0:
            raise ValueError("bits must be positive")
        if num_hashes <= 0:
            raise ValueError("num_hashes must be positive")
        return cls(bits=bits, num_hashes=num_hashes, bit_array=bytearray((bits + 7) // 8))

    def add(self, key: str) -> None:
        for bit_index in self._hash_positions(key):
            byte_index = bit_index // 8
            mask = 1 << (bit_index % 8)
            self.bit_array[byte_index] |= mask

    def might_contain(self, key: str) -> bool:
        for bit_index in self._hash_positions(key):
            byte_index = bit_index // 8
            mask = 1 << (bit_index % 8)
            if (self.bit_array[byte_index] & mask) == 0:
                return False
        return True

    def to_dict(self) -> dict[str, str | int]:
        return {
            "bits": self.bits,
            "num_hashes": self.num_hashes,
            "bit_array_base64": base64.b64encode(bytes(self.bit_array)).decode("ascii"),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "BloomFilter":
        raw = base64.b64decode(payload["bit_array_base64"].encode("ascii"))
        return cls(
            bits=int(payload["bits"]),
            num_hashes=int(payload["num_hashes"]),
            bit_array=bytearray(raw),
        )

    def _hash_positions(self, key: str) -> list[int]:
        key_bytes = key.encode("utf-8")
        positions: list[int] = []
        for i in range(self.num_hashes):
            digest = hashlib.sha256(key_bytes + i.to_bytes(1, "little")).digest()
            positions.append(int.from_bytes(digest[:8], "little") % self.bits)
        return positions
