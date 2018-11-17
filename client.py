# For Client Class -- Code from DAPs only
import asyncio
from aioconsole import ainput

class ClosingException(Exception):
    pass

class ServerClosingException(Exception):
    pass

class BlockChainClient:
    def __init__(self, port):
        self.port = port

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
    client = BlockChainClient(args.port)
    client.run()
