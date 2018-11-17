class Transaction:
    def __init__(self, message, signature):
        self.message = message
        self.signature = signature

class MoneyTransation(Transaction):
    def __init__(self, message, signature):
        super(self).__init__(message, signature)

        self.sender = message['sender_address']
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
