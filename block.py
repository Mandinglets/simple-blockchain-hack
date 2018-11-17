import hashlib
import time

class BlockHeader:
    def __init__(self, index, timestamp, prev_hash, transaction_hash):
        self.index = index
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.transaction_hash = transaction_hash

        self.noice = 0

    def self_hash(self):
        data = str(self.index) + str(self.timestamp) + self.prev_hash + self.transaction_hash + str(self.noice)
        return hashlib.sha256(data.encode()).hexdigest()

class Block:
    def __init__(self, index, timestamp, prev_hash, transaction_list):
        self.transaction_list = transaction_list
        self.root = self.transaction_list_hash()
        self.header = BlockHeader(index, timestamp, prev_hash)

    def transaction_list_hash(self):
        all_data = ' '.join([t.self_hash() for t in self.transaction_list])
        return hashlib.sha256(all_data.encode()).hexdigest()
