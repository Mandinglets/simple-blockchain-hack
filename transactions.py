import hashlib
import pickle

class Transaction:
    def __init__(self, message, signature):
        self.message = message
        self.signature = signature

    def self_hash(self):
        raise NotImplementedError()

class MoneyTransation(Transaction):
    def __init__(self, message, signature):
        super().__init__(message, signature)

        self.sender_address = message['sender_address']
        self.public_key = message['public_key']
        self.receiver_address = message['receiver_address']
        self.value = message['value']

    @classmethod
    def create_reward(cls, receiver_address, reward):
        message = {
            "sender_address": "system",
            "public_key": None,
            "receiver_address": receiver_address,
            "value": reward
        }

        return cls(message, None)

    def __str__(self):
        return f"Money Transaction: {self.sender_address} -> {self.receiver_address} with value: {self.value}"

    def self_hash(self):
        return hashlib.sha256(pickle.dumps(self)).hexdigest()
