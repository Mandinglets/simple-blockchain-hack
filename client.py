# For Client Class -- Code from DAPs only
import sys, asyncio

class NoneException(Exception):
    pass

class ClosingException(Exception):
    pass

async def open_connection(loop):
    reader, writer = await asyncio.open_connection('127.0.0.1',
                                                     8888,loop=loop)
    return reader, writer

async def use_connection(reader, writer):
    try:
        while True:
            console_message = input('>> ')
            if console_message == None or console_message == '':
                continue
            elif console_message == 'close()':
                raise ClosingException()
                
            writer.write(console_message.encode())
            data = await reader.read(100)
            print('Received: %r' % data.decode())
    except ClosingException:
        print('Got close() from user.')
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
        print(e,file=sys.stderr)
    finally:
        loop.close()

if __name__ == '__main__':
    run()
