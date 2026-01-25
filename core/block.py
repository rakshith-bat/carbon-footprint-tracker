import hashlib
import time
import json

class Block:
    def __init__(self, index, transactions, prev_hash, difficulty=2, nonce=0, hash=None, timestamp=None):
        self.index = index
        self.timestamp = timestamp if timestamp else time.time()
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.hash = hash

    def compute_hash(self):
        """Calculate SHA256 hash of block contents"""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce
        }
        data_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(data):
        return Block(
            data["index"],
            data["transactions"],
            data["prev_hash"],
            data.get("difficulty", 2),
            data.get("nonce", 0),
            data.get("hash"),
            data.get("timestamp")
        )