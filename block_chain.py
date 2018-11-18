from transactions import CreateObject

class BlockChain:
    def __init__(self):
        self.data = {
            "content": [],
            "count": 0
        }

    def add_data(self, block):
        self.data['content'].append(block)
        self.data['count'] += 1

    def __str__(self):
        all_contents = '\n\n'.join([str(c) for c in self.data['content']])
        return f"Count: {self.data['count']} \n \n {all_contents}"

    def get_money(self):
        money = {}
        for c in self.data['content']:
            for t in c.transaction_list:
                if isinstance(t, CreateObject):
                    t = t.transaction_to_system
                # Must be in the list
                if not t.sender_address == "system":
                    money[t.sender_address] -= t.value

                if t.receiver_address in money:
                    money[t.receiver_address] += t.value
                elif not t.receiver_address == "system":
                    money[t.receiver_address] = t.value

        return money

    def total_transaction_list(self, t_list):
        change = {}
        for t in t_list:
            if isinstance(t, CreateObject):
                t = t.transaction_to_system
            # Must be in the list
            if not t.sender_address == "system":
                if t.sender_address in change:
                    change[t.sender_address] -= t.value
                else:
                    change[t.sender_address] = -t.value

            if t.receiver_address in change:
                change[t.receiver_address] += t.value
            elif not t.receiver_address == "system":
                change[t.receiver_address] = t.value
        return change
