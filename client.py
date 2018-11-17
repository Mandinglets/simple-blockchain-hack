# For Client Class -- Code from DAPs only
import asyncio

class ClosingException(Exception):
    pass

async def open_connection(loop):
    reader, writer = await asyncio.open_connection('127.0.0.1',
                                                     8888,loop=loop)
    return reader, writer

async def use_connection(reader, writer):
    try:
        while True:
            msg = input('>> ')
            if msg == None or msg == '':
                continue

            writer.write(msg.encode())
            data = await reader.read(4048)
            print('Received: %r' % data.decode())
    except KeyboardInterrupt:
        print('Got Ctrl-C from user.')
    finally:
        writer.close()

def run():
    try:
        loop = asyncio.get_event_loop()
        reader,writer=loop.run_until_complete(open_connection(loop))
        loop.run_until_complete(use_connection(reader, writer))
    except Exception as e:
        print("Getting some problem")
    finally:
        loop.close()

if __name__ == '__main__':
    run()
