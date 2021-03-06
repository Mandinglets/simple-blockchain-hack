# For Client Class -- Code from DAPs only
"""
Run API
Run server
Run Client with port number
"""
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
import warnings
import numpy as np

from helper import StupidPublicKey
from transactions import MoneyTransation, CreateObject, GetDataObject, ResponseDataObject
from block import Block
from block_chain import BlockChain

import time
import random

from aiohttp import web
import aiohttp
import aiohttp_jinja2
import jinja2
from PIL import Image
import io

import os

class ClosingException(Exception):
    pass

class ServerClosingException(Exception):
    pass

class BlockChainClient:
    def __init__(self, port, crypto_curve, signature_algo,start_reward, decrease_reward, local_img_path, api_addr):

        self.PORT = port
        self.CURVE = crypto_curve
        self.SIGNATURE_ALGORITHM = signature_algo
        self.DECREASE_REWAD = decrease_reward
        self.IMG_PATH = local_img_path
        self.API_ADDR = api_addr

        self.reward = start_reward

        # Start generating private & public key
        self._private_key = ec.generate_private_key(self.CURVE, default_backend())
        self.public_key_obj = self._private_key.public_key()
        self.public_key = StupidPublicKey(self.public_key_obj.public_numbers().x,
                                            self.public_key_obj.public_numbers().y)

        self.address = self.generate_address(self.public_key)
        self.chain = BlockChain()
        self.mempool = []

        self.is_mining = False
        self.fucking_delay = 0
        self.create_fee = 5

        self.img_library = {}
        self.own_data = []

        # Create a local_img folder
        if not os.path.isdir(self.IMG_PATH):
            os.mkdir(self.IMG_PATH)


    async def send_to_server(self, server):
        while True:
            msg = await ainput('')
            if msg == None or msg == '':
                continue

            await self.parse_input(msg)

    async def get_data_server(self, server, client):
        while True:
            data = await client.read(4048)
            if server.transport.is_closing():
                print("Closing")

            if len(data) == 0:
                raise ServerClosingException()

            await self.parse_server_message(data)

    async def send_object_server(self, obj):
        self.server.write(pickle.dumps(obj))
        await self.server.drain()

    async def send_transations(self, address, value):
        # Check Address
        if address == self.address:
            return "That is your address"
        elif self.check_address(address):
            if not self.chain.get_money().get(self.address, 0) >= value:
                return "Not enough Fund LOL"
            else:
                message = {
                    "sender_address": self.address,
                    "public_key": self.public_key,
                    "receiver_address": address,
                    "value": value
                }

                sig = self._private_key.sign(pickle.dumps(message), self.SIGNATURE_ALGORITHM)
                send_object = MoneyTransation(message, sig)

                # Sending message
                await self.send_object_server(send_object)
        else:
            return "Address not correct"

    async def create_object(self):
        if not self.chain.get_money().get(self.address, 0) >= self.create_fee:
            return "Not enough Fund LOL"

        message = {
            "sender_address": self.address,
            "public_key": self.public_key,
            "receiver_address": "system",
            "value": self.create_fee
        }
        sig = self._private_key.sign(pickle.dumps(message), self.SIGNATURE_ALGORITHM)
        system_transaction = MoneyTransation(message, sig)

        # Create numpy array 1x100
        new_data = np.random.randn(1, 100)
        data_hash = hashlib.sha256(pickle.dumps(new_data.tostring())).hexdigest()
        self.img_library[data_hash] = new_data

        message = {
            "sender_address": self.address,
            "public_key": self.public_key,
            "data_hash": data_hash
        }

        sig = self._private_key.sign(pickle.dumps(message), self.SIGNATURE_ALGORITHM)
        create_obj = CreateObject(message, sig, system_transaction)

        await self.send_object_server(create_obj)

    async def parse_input(self, command):
        data = command.split(' ')
        if data[0] == "pay":
            assert len(data) == 3

            address = data[1]
            value = float(data[2])

            await self.send_transations(address, value)

        elif data[0] == "show_chain":
            asyncio.ensure_future(self.print_chain())
        elif data[0] == "show_mempool":
            print(self.mempool)
        elif data[0] == "show_money":
            print(self.chain.get_money())
        elif data[0] == "show_owner":
            print(self.chain.get_owner())
        elif data[0] == "send_object_request":
            await self.get_own_data()
        elif data[0] == "show_library":
            asyncio.ensure_future(self.print_library())
        elif data[0] == "show_own_data":
            asyncio.ensure_future(self.print_own_data())
        else:
            print("Command not Found")

    async def print_own_data(self):
        for v in self.own_data:
            print(f"{v[:, :3]}")

    async def print_library(self):
        for k, v in self.img_library.items():
            print(f"{k}: {v[:, :3]}")

    async def create_block(self, data):
        self.mempool.append(data)
        self.mempool.append(MoneyTransation.create_reward(self.address, self.reward))

        if self.check_multiple_transactions(self.mempool):
            block = Block(self.chain.data['count'],
                          time.time(),
                          self.chain.data['content'][-1].header.self_hash(),
                          self.mempool)

            self.mempool = []
            self.is_mining = True
            self.mine_task = asyncio.ensure_future(self.mine(block))

    async def print_chain(self):
        print(f"Count: {self.chain.data['count']}")
        for c in self.chain.data['content']:
            print('\n\n')
            print(c)
            await asyncio.sleep(0.0)

    async def get_own_data(self):
        warnings.warn("might block")
        owned_hash = self.chain.get_owner().get(self.address, [])
        for o in owned_hash:
            message = {
                "sender_address": self.address,
                "public_key": self.public_key
            }
            sig = self._private_key.sign(pickle.dumps(message), self.SIGNATURE_ALGORITHM)
            await self.send_object_server(GetDataObject(message, sig, o))

    async def parse_server_message(self, data):
        data = pickle.loads(data)

        if isinstance(data, MoneyTransation):
            # Start creating your own block
            if not self.check_signature(data.message, data.signature):
                print("Transaction Not accepted")

            else:
                if self.is_mining:
                    self.mempool.append(data)
                else:
                    await self.create_block(data)

        elif isinstance(data, str):
            if data == "FIRST_USER":
                print("God has chosen you to mine the genesis block")
                genesis_block = Block(0,
                                      time.time(),
                                      "0000000000000000000000000000000000000000000000000000000000000000",
                                      [MoneyTransation.create_reward(self.address, self.reward)])

                # Mine the block
                self.is_mining = True
                self.mine_task = asyncio.ensure_future(self.mine(genesis_block))

            if data == "REQUEST_BLOCKCHAIN":
                print("Requestion a blockchain")
                await self.send_object_server(self.chain)

        elif isinstance(data, Block):
            print("Get a block")
            if self.check_block(data):
                print("Add to the chain")
                self.chain.add_data(data)

                self.mine_task.cancel()
                self.is_mining = False

                # Everytime chain is updated get the new data. Inefficient
                warnings.warn("Not efficient requesting everytime")
                self.own_data = []
                await self.get_own_data()

            else:
                print("Can't Add sth wrong")

        elif isinstance(data, BlockChain):
            if self.chain.data['count'] == 0:
                self.chain = data
                print("Chain Added")
        elif isinstance(data, CreateObject):
            # who ever won the mine get to save the object
            if not self.check_signature(data.message, data.signature):
                print("Create object isn't accepted")
            elif not self.check_signature(data.transaction_to_system.message, data.transaction_to_system.signature):
                print("transaction obj in create object isn't right")
            else:
                if self.is_mining:
                    self.mempool.append(data)
                else:
                    await self.create_block(data)
        elif isinstance(data, GetDataObject):
            if self.check_signature(data.message, data.signature):
                if data.wanted_hash in self.img_library:
                    response =  ResponseDataObject(self.img_library[data.wanted_hash], data.sender_address)
                    await self.send_object_server(response)
        elif isinstance(data, ResponseDataObject):
            if data.send_to_address == self.address:
                if hashlib.sha256(pickle.dumps(data.data.tostring())).hexdigest() in self.chain.get_owner()[self.address]:
                    print("Get Data!!")
                    self.own_data.append(data.data)
                else:
                    print("Hash isn't right")
        else:
            print("Getting Weird Object")
            print(data)

    async def mine(self, block):
        header = block.header
        num_zero = self.current_difficulty()
        warnings.warn("Haven't implementaed difficulty")

        block_hash = header.self_hash()
        while not block_hash[:num_zero] == '0' * num_zero:
            header.nouce += 1
            block_hash = header.self_hash()
            await asyncio.sleep(self.fucking_delay)

        block.header = header
        self.is_mining = False

        await self.send_object_server(block)

    def current_difficulty(self):
        return 4

    def check_address(self, address):
        # Just a wrapper
        try:
            base58.b58decode_check(address)
        except ValueError:
            return False
        else:
            return True

    def check_block(self, block):
        if not self.check_header(block.header):
            return False

        if not block.header.transaction_hash == block.transaction_list_hash():
            print("BLOCK: transaction hash are not the same.")
            return False

        # Check transaction money
        if not self.check_multiple_transactions(block.transaction_list):
            return False

        return True

    def check_header(self, header):
        if not header.index == self.chain.data['count']:
            print("HEADER: header index not currect")
            return False

        if not self.chain.data['count'] == 0:
            latest_head = self.chain.data['content'][-1].header
            if not latest_head.timestamp < header.timestamp:
                print("HEADER: wrong time stamp")
                return False

            if not latest_head.self_hash() == header.prev_hash:
                print("HEADER: wrong previous hash")
                return False

        # Check for PoW
        if not header.self_hash()[:self.current_difficulty()] == '0' * self.current_difficulty():
            print("HEADER: wrong proof of work")
            return False

        return True

    def check_multiple_transactions(self, transaction_list):
        # Checking for weird funds
        total_money = self.chain.get_money()
        change = self.chain.total_transaction_list(transaction_list)

        # Might be a problem of dropping everyting when one fail :(
        if any(total_money.get(addr, 0) + val < 0 for addr, val in change.items()):
            print("LIST TRANSACTION: run out of funds")
            return False

        # Check for ownership
        warnings.warn("Check for ownership not done")

        if not all(self.check_signature(t.message, t.signature) for t in transaction_list):
            print("LIST TRANSACTION: wrong signature")
            return False

        return True

    async def start_connection(self, server, client):
        await asyncio.gather(self.get_data_server(server, client), self.send_to_server(server))

    async def open_connection(self, loop):
        client, server = await asyncio.open_connection('127.0.0.1',
                                                         8888,loop=loop)
        return client, server

    def check_signature(self, message, signature):
        byte_message = pickle.dumps(message)

        if message['sender_address'] == "system":
            return True

        if not message['sender_address'] == self.generate_address(message['public_key']):
            print("Sender Address isn't the same as the generate addresss")
            return False

        pub = ec.EllipticCurvePublicNumbers(
                message['public_key'].x,
                message['public_key'].y,
                self.CURVE
            ).public_key(default_backend())

        try:
            pub.verify(signature, byte_message, self.SIGNATURE_ALGORITHM)
        except cryptography.exceptions.InvalidSignature:
            return False
        else:
            return True

    def generate_address(self, public):
        # Using the hash stuff from bitcoin wiki
        actual_key = '02' + format(public.x, '064x')

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

    async def delete_files(self):
        filelist = [f for f in os.listdir(self.IMG_PATH) if f.endswith(".png") ]
        for f in filelist:
            os.remove(os.path.join(self.IMG_PATH, f))
            await asyncio.sleep(0.0)

    async def save_image(self, bytes, save_path):
        await asyncio.sleep(0.0)

    async def download_imgs(self, np_array):
        async with aiohttp.ClientSession() as session:

            content_type = 'image/jpeg'
            headers = {'content-type': content_type}

            async with session.post(self.API_ADDR, data=np_array.tostring(), headers=headers) as resp:
                print(resp.status)
                import sys
                bytes = await resp.content.read(20000)
                print(sys.getsizeof(bytes))
                save_path = os.path.join(self.IMG_PATH, f"{hashlib.sha256(bytes).hexdigest()}.png")

                f = open(save_path, 'wb')
                f.write(bytearray(bytes))
                f.close()

                return f"{hashlib.sha256(bytes).hexdigest()}.png"

    async def fetch_all_imgs(self):
        all_path = []
        for a in self.own_data:
            save_path = await self.download_imgs(a)
            all_path.append(save_path)
            await asyncio.sleep(0.0)
        return all_path

    @aiohttp_jinja2.template('transaction_page.jinja2')
    async def main_page(self, request):
        # Everytime main page is updated.
        # Delete everyting in folder
        print("runnnnn")
        asyncio.ensure_future(self.delete_files())
        # download a new one that will return the path
        file_paths = await self.fetch_all_imgs()
        print(file_paths)

        names = [f[:8]for f in file_paths]
        print(names)

        return {
            'address': self.address,
            'static_path_img': request.app.router['img'].url_for(filename=''),
            'static_path_scl': request.app.router['scl'].url_for(filename=''),
            'static_path_css': request.app.router['css'].url_for(filename=''),
            'static_path_jqjs': request.app.router['jqjs'].url_for(filename=''),
            'static_path_bsjs': request.app.router['boot_js'].url_for(filename=''),
            'static_path_esjs': request.app.router['esa_js'].url_for(filename=''),
            'self_address': self.address,
            'current_money': self.chain.get_money().get(self.address, 0.0),
            'img_paths': file_paths,
            'img_name': names
        }

    async def create_obj_web(self, request):
        data = await request.post()
        result = await self.create_object()
        return web.Response(text=result)

    async def transact_web(self, request):
        data = await request.post()

        address = data['address']
        value = float(data['val'])

        result = await self.send_transations(address, value)
        return web.Response(text=result)

    async def init_webserver(self, port):
        app = web.Application()

        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates/'))

        routes = [
            web.get('/', self.main_page),
            web.post('/transact', self.transact_web),
            web.post('/create_obj', self.create_obj_web),
        ]
        app.add_routes(routes)

        app.router.add_static("/sample_img", 'templates/images', name="img")
        app.router.add_static("/scrolling", 'templates/js', name="scl")
        app.router.add_static("/css", 'templates/css', name="css")
        app.router.add_static("/jquery_js", 'templates/vendor/jquery', name="jqjs")
        app.router.add_static("/boot_js", 'templates/vendor/bootstrap/js', name="boot_js")
        app.router.add_static("/es_js", 'templates/vendor/jquery-easing/', name="esa_js")

        runner = web.AppRunner(app)

        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()

    def run(self):
        try:
            self.loop = asyncio.get_event_loop()
            self.client, self.server = self.loop.run_until_complete(self.open_connection(self.loop))
            self.loop.run_until_complete(self.init_webserver(self.PORT))
            self.loop.run_until_complete(self.start_connection(self.server, self.client))
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
    START_REWARD = 50.0
    DECREASE_REWARD = 10

    client = BlockChainClient(args.port, CURVE, SIGNATURE_ALGORITHM, START_REWARD, DECREASE_REWARD, "templates/images", "http://0.0.0.0:5000/api/test")
    print(f"Running on Address: {client.address}")
    client.run()
