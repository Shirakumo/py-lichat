from . import symbol
from . import update
from . import wire
import time
import select
import socket
import base64

class ConnectionFailed(Exception):
    def __init__(self, update=None, message='Connection failed.'):
        self.update = update
        if update and get(update, 'message'):
            message = get(update, 'message')
        super().__init__(message)

class Channel:
    def __init__(self, name):
        self.name = name
        self.users = set()
        self.info = {}

    def join(self, name):
        self.users.add(name)

    def leave(self, name):
        self.users.discard(name)

    def __getitem__(self, key):
        return self.info.get(key)

    def __setitem__(self, key, value):
        self.info[key] = value
        return value

class Emote:
    def __init__(self, name, content_type, payload):
        self.name = name
        self.content_type = content_type
        self.payload = payload
    
class Client:
    def __init__(self, username=None):
        self.username = username
        self.servername = None
        self.connected = False
        self.extensions = []
        self.id = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chunks = []
        self.channels = {}
        self.emotes = {}

        def connect(self, u):
            self.connected = True
            self.username = u['from']
            self.extensions = [x for x in u.extensions if x in update.extensions]

        def disconnect(self, u):
            self.connected = False
            self.channels.clear()
            self.chunks = []
            self.extensions = []
            self.socket.close()
        
        def ping(self, u):
            self.send(update.Pong)

        def join(self, u):
            if self.servername == None:
                self.servername = u.channel
                if self.is_supported('shirakumo-emotes'):
                    self.send(update.Emotes, names=list(self.emotes.keys()))
            if u['from'] == self.username:
                self.channels[u.channel] = Channel(u.channel)
                if self.is_supported('shirakumo-channel-info'):
                    self.send(update.ChannelInfo, channel=u.channel)
                if self.is_supported('shirakumo-backfill'):
                    self.send(update.Backfill, channel=u.channel)
            self.channels[u.channel].join(u['from'])

        def leave(self, u):
            if u['from'] == self.username:
                self.channels[u.channel]
            else:
                self.channels[u.channel].leave(u['from'])

        def emote(self, u):
            self.emotes[u.name] = Emote(u.name, u['content-type'], base64.b64decode(u.payload))

        def channelinfo(self, u):
            channel = self.channels.get(u.channel, None)
            if channel != None:
                channel[u.key] = u.value
            
        self.handlers = {
            update.Update: [],
            update.Connect: [connect],
            update.Disconnect: [disconnect],
            update.Ping: [ping],
            update.Join: [join],
            update.Leave: [leave],
            update.Emote: [emote],
            update.SetChannelInfo: [channelinfo]
        }

    def add_handler(self, update, fun):
        if update not in self.handlers:
            self.handlers[update] = []
        self.handlers[update].append(fun)

    def clock():
        int(time.time()) + 2208988800

    def next_id(self):
        self.id = self.id+1
        return self.id

    def is_supported(self, extension):
        return extension in self.extensions

    def connect(self, host, port=1111, timeout=10.0):
        self.connect_raw(host, port)
        self.send(update.Connect, version=update.version, extensions=update.extensions)
        updates = self.recv(timeout)
        if updates:
            if type(updates[0]) is not update.Connect:
                raise ConnectionFailed(update=update)
            for instance in updates:
                self.handle(instance)
        else:
            raise ConnectionFailed(message="Timeout")

    def send(self, type, **args):
        args['from'] = self.username
        args['clock'] = Client.clock()
        args['id'] = self.next_id()
        instance = update.make_instance(type, **args)
        self.send_raw(wire.to_string(instance.to_list()))
        return instance.id

    def recv(self, timeout=0):
        strings = self.recv_raw(timeout)
        updates = []
        for string in strings:
            (update, _i) = read_update(string)
            if update != None:
                updates.append(update)
        return updates

    def handle(self, instance):
        handlers = self.handlers.get(instance.__class__, None)
        if handlers == None:
            handlers = self.handlers[update.Update]
        for handler in handlers:
            handler(self, instance)

    def loop(self):
        while self.connected:
            for update in self.recv(1.0):
                self.handle(update)

    def connect_raw(self, host, port=1111):
        self.socket.connect((host, port))
        self.socket.setblocking(0)

    def send_raw(self, string):
        totalsent = 0
        binary = string.encode('utf-8') + b'\0'
        length = len(binary)
        while totalsent < length:
            try:
                sent = self.socket.send(binary[totalsent:])
                if sent == 0:
                    raise RuntimeError('socket connection broken')
                totalsent = totalsent + sent
            except socket.error as e:
                if e.errno != errno.EAGAIN:
                    raise e
                select.select([], [self.socket], [])
        
    def recv_raw(self, timeout=0):
        read = select.select([self.socket], [], [], timeout)
        if read[0]:
            found_end = False
            chunk = self.socket.recv(4096).decode('utf-8')
            while 0 < len(chunk):
                self.chunks.append(chunk)
                if '\0' in chunk:
                    found_end = True
                    break
                select.select([self.socket], [], [])
                chunk = self.socket.recv(4096).decode('utf-8')
            if found_end:
                return self.stitch()
        return []

    def stitch(self):
        parts = ''.join(self.chunks).split('\0')
        self.chunks = [parts.pop()]
        return parts

def read_update(string, i=0):
    (dat, i) = wire.from_string(string, i)
    if type(dat) == list and 0 < len(dat):
        instance = update.make_instance_plist(dat[0], dat[1:])
        return (instance, i)
    return (None, i)    
