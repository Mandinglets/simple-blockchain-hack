# For Client Class -- Code from DAPs only
import asyncio
from aioconsole import ainput

class ClosingException(Exception):
    pass

class ServerClosingException(Exception):
    pass

async def send_to_server(server):
    while True:
        msg = await ainput('')
        if msg == None or msg == '':
            continue
        server.write(msg.encode())
        await server.drain()


async def get_data_server(server, client):
    while True:
        data = await client.read(4048)
        if server.transport.is_closing():
            print("Closing")

        if len(data) == 0:
            raise ServerClosingException()

        print(f"Get the message {data.decode()}")

async def start_connection(server, client):
    await asyncio.gather(get_data_server(server, client), send_to_server(server))

async def open_connection(loop):
    client, server = await asyncio.open_connection('127.0.0.1',
                                                     8888,loop=loop)
    return client, server


try:
    loop = asyncio.get_event_loop()
    client, server=loop.run_until_complete(open_connection(loop))
    loop.run_until_complete(start_connection(server, client))
except ServerClosingException as e:
    print("Server just closed")
finally:
    loop.close()
