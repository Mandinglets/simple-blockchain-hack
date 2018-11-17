# For Server Class -- Using the code from DAPs Class.
import asyncio
import pickle

all_clients = set([])

async def handle_connection(reader, writer):
    client_addr = writer.get_extra_info('peername')
    print(f"New client {client_addr}")

    if len(all_clients) == 0:
        # First Player Holy Shit
        message = "FIRST_USER"
        writer.write(pickle.dumps(message))
        await writer.drain()
    else:
        # Not always tho because set isn't ordered element.
        oldest_user = list(all_clients)[0]
        oldest_user.write(pickle.dumps("REQUEST_BLOCKCHAIN"))
        await oldest_user.drain()

    all_clients.add(writer)

    while True:
        data = await reader.read(4048)
        if data is None or len(data) == 0:
            break

        print(f"Get data {type(data)}")

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
