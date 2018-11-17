class BlockChain:
    def __init__(self):
        self.data = {
            "content": [],
            "count": 0
        }

    def add_data(self, block):
        self.data['content'].append(block)
        self.data['count'] += 1
