# For Client Class -- Code from DAPs only
import asyncio
from aioconsole import ainput

import cryptography
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

import hashlib
import codecs
import base58

import pickle
from helper import StupidPublicKey

class ClosingException(Exception):
    pass

class ServerClosingException(Exception):
    pass

class BlockChainClient:
    def __init__(self,
                    port,
                    crypto_curve,
                    signature_algo,
                    start_reward,
                    decrease_reward):

        self.PORT = port
        self.CURVE = crypto_curve
        self.SIGNATURE_ALGORITHM = signature_algo
        self.DECREASE_REWAD = decrease_reward

        self.reward = start_reward

        # Start generating private & public key
        self._private_key = ec.generate_private_key(self.CURVE, default_backend())
        self.public_key_obj = self._private_key.public_key()
        self.public_key = StupidPublicKey(self.public_key_obj.public_numbers().x,
                                            self.public_key_obj.public_numbers().y)

        self.address = self.generate_address()

    def check_signature(self, message, signature):
        byte_message = pickle.dumps(message)

        try:
            pub.verify(signature, byte_message, self.UNIVERSAL_SIG_ALGO)
        except cryptography.exceptions.InvalidSignature:
            return False
        finally:
            return True

    def generate_address(self):
        # Using the hash stuff from bitcoin wiki
        actual_key = '02' + format(self.public_key.x, '064x')

        sh = hashlib.sha256()
        rip = hashlib.new('ripemd160')

        sh.update(codecs.decode(actual_key, 'hex'))
        rip.update(sh.digest())

        double_hash = '00' + rip.hexdigest()
        sh.update(codecs.decode(double_hash, 'hex'))

        check_sum_1 = hashlib.sha256(codecs.decode(double_hash, 'hex'))
        check_sum_2 = hashlib.sha256(check_sum_1.digest())
        check_sum = check_sum_2.hexdigest()[:8]

        bit_25_address = double_hash + check_sum
        final_address = base58.b58encode(codecs.decode(bit_25_address, 'hex'))
        return final_address.decode()

    async def send_to_server(self, server):
        while True:
            msg = await ainput('')
            if msg == None or msg == '':
                continue
            server.write(msg.encode())
            await server.drain()

    async def get_data_server(self, server, client):
        while True:
            data = await client.read(4048)
            if server.transport.is_closing():
                print("Closing")

            if len(data) == 0:
                raise ServerClosingException()

            print(f"Get the message {data.decode()}")

    async def start_connection(self, server, client):
        await asyncio.gather(self.get_data_server(server, client), self.send_to_server(server))

    async def open_connection(self, loop):
        client, server = await asyncio.open_connection('127.0.0.1',
                                                         8888,loop=loop)
        return client, server

    def run(self):
        try:
            self.loop = asyncio.get_event_loop()
            client, server = self.loop.run_until_complete(self.open_connection(self.loop))
            self.loop.run_until_complete(self.start_connection(server, client))
        except ServerClosingException as e:
            print("Server just closed")
        finally:
            self.loop.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fun Fun Bitcoin')
    parser.add_argument('-p', '--port', dest='port', help='Define the port name')
    args = parser.parse_args()

    # Getting the configureation
    CURVE = ec.SECP256K1()
    SIGNATURE_ALGORITHM = ec.ECDSA(hashes.SHA256())
    START_REWARD = 50
    DECREASE_REWARD = 10



    client = BlockChainClient(args.port, CURVE, SIGNATURE_ALGORITHM, START_REWARD, DECREASE_REWARD)
    print(f"Running on Address: {client.address}")
    client.run()
