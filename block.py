import hashlib
import time

class BlockHeader:
    def __init__(self, index, timestamp, prev_hash, transaction_hash):
        self.index = index
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.transaction_hash = transaction_hash
        self.nouce = 0

    def self_hash(self):
        data = str(self.index) + str(self.timestamp) + self.prev_hash + self.transaction_hash + str(self.nouce)
        return hashlib.sha256(data.encode()).hexdigest()

    def __str__(self):
        return f"Index: {self.index} \nTimestamp: {str(time.ctime(int(self.timestamp)))} \nPrev Hash: {self.prev_hash} \nTransaction Hash: {self.transaction_hash}"

class Block:
    def __init__(self, index, timestamp, prev_hash, transaction_list):
        self.transaction_list = transaction_list
        self.root = self.transaction_list_hash()
        self.header = BlockHeader(index, timestamp, prev_hash, self.root)

    def transaction_list_hash(self):
        all_data = ''.join([t.self_hash() for t in self.transaction_list])
        return hashlib.sha256(all_data.encode()).hexdigest()

    def __str__(self):
        return f"Block: Header: \n{self.header} \nTransaction List: {self.transaction_list}"
