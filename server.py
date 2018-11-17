# For Server Class -- Using the code from DAPs Class.
import sys, asyncio

all_clients = set([])

async def handle_connection(reader, writer):
    all_clients.add(writer)
    client_addr = writer.get_extra_info('peername')
    print(f"New client {client_addr}")

    while True:
        data = await reader.read(4048)
        for other_writer in all_clients:
            other_writer.write(data)
            await other_writer.drain()

    print("Close the client socket")
    writer.close()
    all_clients.remove(writer)

loop = asyncio.get_event_loop()
coro = asyncio.start_server(handle_connection,'127.0.0.1',
                                            8888,loop=loop)
server = loop.run_until_complete(coro)

try:
    loop.run_forever()
except KeyboardInterrupt:
    print('\nGot keyboard interrupt, shutting down')

for task in asyncio.Task.all_tasks():
    task.cancel()

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
