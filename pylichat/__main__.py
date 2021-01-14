from .client import Client
from .update import *
import select
import sys

def handle_input(client, line):
    if line[0] != '/':
        client.send(Message, channel=client.channel, text=line)
    else:
        parts = line.split(' ', 1)
        command = parts[0]
        argument = parts[1]
        if command == '/join':
            client.send(Join, channel=argument)
        elif command == '/leave':
            if argument == '': argument = client.channel
            client.send(Leave, channel=argument)
        elif command == '/create':
            if argument == '':
                client.send(Create)
            else:
                client.send(Create, channel=argument)
        else:
            print('\n Unknown command {0}'.format(command))

def loop(client):
    readable,_,_ = select.select([sys.stdin,client.socket],[],[])
    if readable == []:
        pass
    elif client.socket in readable:
        for update in client.recv():
            client.handle(update)
    else:
        line = sys.stdin.readline().rstrip('\n')
        if len(line) != 0:
            handle_input(client, line)

def on_misc(client, u):
    if isinstance(u, Failure):
        print('ERROR: {0}'.format(u.text))

def on_message(client, u):
    print('[{0}] <{1}> {2}'.format(u.channel, u['from'], u.text))

def on_join(client, u):
    if u['from'] == client.username:
        client.channel = u.channel
        print('[{0}] ** {1} Joined'.format(u.channel, u['from']))

def on_leave(client, u):
    if client.channel == u.channel:
        client.channel = next(iter(client.channels))
        print('[{0}] ** {1} Left'.format(u.channel, u['from']))

class MyClient(Client):
    __slots__ = 'channel'

def main(username=None, host="chat.tymoon.eu", port=1111):
    client = MyClient(username)
    client.channel = None
    client.add_handler(Update, on_misc)
    client.add_handler(Message, on_message)
    client.add_handler(Join, on_join)
    client.add_handler(Leave, on_leave)
    client.connect(host, port)
    
    while client.connected:
        loop(client)

if __name__ == '__main__':
    main(*sys.argv[1:])
