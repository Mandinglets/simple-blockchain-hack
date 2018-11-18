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

    def __repr__(self):
        return str(self)

    def self_hash(self):
        return hashlib.sha256(pickle.dumps(str(self))).hexdigest()

class GetDataObject(Transaction):
    def __init__(self, message, signature, wanted_hash):
        super().__init__(message, signature)
        self.sender_address = message['sender_address']
        self.public_key = message['public_key']
        self.wanted_hash = wanted_hash

    def self_hash(self):
        pass

    def __str__(self):
        return f"GetDataObject: Sender Address: {self.sender_address} wanting {self.wanted_hash}"

    def __repr__(self):
        return str(self)

class ResponseDataObject:
    def __init__(self, data, send_to_address):
        self.data = data
        self.send_to_address = send_to_address

    def self_hash(self):
        pass

    def data_hash(self):
        return hashlib.sha256(pickle.dumps(self.data.tostring())).hexdigest()

    def __str__(self):
        return f"Response Object: Send to Address: {self.send_to_address}"

    def __repr__(self):
         return str(self)

class CreateObject(Transaction):
    def __init__(self, message, signature, transaction_to_system):
        super().__init__(message, signature)

        self.sender_address = message['sender_address']
        self.public_key = message['public_key']
        self.transaction_to_system = transaction_to_system
        self.data_hash = message['data_hash']

    def __str__(self):
        return f"Create Object: from {self.sender_address}, with transaction {str(self.transaction_to_system)}"

    def __repr__(self):
        return str(self)

    def self_hash(self):
        return hashlib.sha256(pickle.dumps(str(self))).hexdigest()

class SendObject(Transaction):
    def __init__(self, message, signature):
        super().__init__(message, signature)

        self.sender_address = message['sender_address']
        self.public_key = message['public_key']
        self.receiver_address = message['receiver_address']
        self.hash_object = message['hash_object']

    def self_hash(self):
        return hashlib.sha256(pickle.dumps(str(self))).hexdigest()

    def __str__(self):
        return f"Send Hash Object({self.hash_object[:4]}..): from {self.sender_address} -> {self.receiver_address}"

    def __repr__(self):
        return str(self)
