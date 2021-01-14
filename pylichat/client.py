from . import symbol
from . import update
from . import wire
from pathlib import Path
import collections.abc
import time
import select
import socket
import base64
import mimetypes

class ConnectionFailed(Exception):
    """Exception thrown when the connection attempt to the server fails for some reason.

    May hold an update field with the Update instance that caused
    the connection failure, if the server was reachable, but
    connection failed for another reason.
    """
    def __init__(self, update=None, message='Connection failed.'):
        self.update = update
        if update and get(update, 'message'):
            message = get(update, 'message')
        super().__init__(message)

class CaseInsensitiveDict(collections.abc.MutableMapping):
    """A dict where key lookup ignores case (Unicode case-folding as per str.casefold())"""
    __slots__ = 'data'

    def __init__(self, d=dict()):
        self.data = {k.casefold(): (k, v) for k, v in d.items()}

    def __contains__(self, k):
        return k.casefold() in self.data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, k):
        return self.data[k.casefold()][1]

    def __iter__(self):
        return (v[0] for v in self.data.values())

    def __setitem__(self, k, v):
        self.data[k.casefold()] = (k, v)

    def __delitem__(self, k):
        del self.data[k.casefold()]

    def __repr__(self):
        return f"CaseInsensitiveDict({dict(self)})"

class CaseInsensitiveSet(collections.abc.MutableSet):
    """A set where lookup ignores case (Unicode case-folding as per str.casefold())"""
    __slots__ = 'data'

    def __init__(self, s=set()):
        self.data = {i.casefold(): i for i in s}

    def __contains__(self, i):
        return i.casefold() in self.data

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return (v for v in self.data.values())

    def add(self, i):
        self.data[i.casefold()] = i

    def discard(self, i):
        self.data.pop(i.casefold(), None)

    def __repr__(self):
        return f"CaseInsensitiveSet({set(self)})"

class Channel:
    """Representation of a channel the client is in.

    Channels have a name, a list of users, and a dictionary
    of channel information that is stored on servers with the
    shirakumo-channel-info extension.

    You may access the channel information by accessing the
    channel object like a dictionary.
    """
    def __init__(self, name):
        self.name = name
        self.users = CaseInsensitiveSet()
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
    """Representation of an emote the server sent back.

    An emote has a name, a content_type (as a mime-type string)
    and a binary payload that describes the actual image data
    """
    def __init__(self, name, content_type, payload):
        self.name = name
        self.content_type = content_type
        self.payload = payload

    def from_file(filename):
        with open(filename, 'rb') as file:
            name = Path(filename).stem
            (content_type,) = mimetypes.guess_type(file, False)
            if content_type == None:
                return None
            return Emote(name, content_type, file.read())

    def offload(self, directory):
        with open(directory+'/'+self.filename(), 'wb') as file:
            file.write(self.payload)

    def filename(self):
        if not mimetypes.inited:
            mimetypes.init()
        self.name+mimetypes.guess_extension(self.content_type, False)
    
class Client:
    """A basic Lichat client using TCP sockets.

    The client has a username, password, servername, a
    connected flag, supperted extensions list, channels
    dictionary, and emotes dictionary.
    
    The client will take care of basic connection
    establishment and maintenance of information.
    All you need to do is actually display and access
    the information present in the client, and sent
    through updates.

    In order to add a handler function for an update,
    you may add a handler using add_handler.
    
    Updates can be sent out with send, received
    with recv, and handled with handle.

    When constructed the client will not attempt
    connection. Connection has to be manually
    initiated with the connect function.
    """
    
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.servername = None
        self.connected = False
        self.extensions = []
        self.id = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chunks = []
        self.channels = CaseInsensitiveDict()
        self.emotes = CaseInsensitiveDict()

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
                self.send(update.Users, channel=u.channel)
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
        """Adds a handler function for the given update type.

        Supplied to the handler function are the client
        and the update objects. add_handler expects an Update
        class as argument for which the handler function
        is invoked. Note that only exact type matches are
        dispatched, the class hierarchy is ignored. You
        may however install a handler on Update, which
        will be invoked for every update, regardless of
        actual type.
        """
        if update not in self.handlers:
            self.handlers[update] = []
        self.handlers[update].append(fun)

    def clock():
        """Returns the current time in universal-time"""
        int(time.time()) + 2208988800

    def next_id(self):
        """Returns a new unique ID."""
        self.id = self.id+1
        return self.id

    def is_supported(self, extension):
        """Returns true if the given extension is supported by client and server."""
        return extension in self.extensions

    def offload_emotes(self, directory):
        """Writes all emotes as files to the given directory."""
        for emote in self.emotes:
            emote.offload(directory)
    
    def reload_emotes(self, directory):
        """Load all files from the directory into the emote database."""
        for path in os.listdir(directory):
            emote = Emote.from_file(directory+'/'+path)
            if emote != None:
                self.emotes[emote.name] = emote

    def connect(self, host, port=1111, timeout=10.0, username=None, password=None):
        """Attempts to establish a connection to the given server.

        You may also pass in the username and password,
        as well as a timout for the connection attempt.
        This will perform a full connection handshake.
        After this you should start processing updates
        immediately.

        If you want to receive the Connect update, you
        must install a handler for it prior to calling
        this function.
        
        Should the connection attempt fail for whatever
        reason, a ConnectionFailed exception is thrown.
        """
        if username != None: self.username = username
        if password != None: self.password = password
        self.connect_raw(host, port)
        self.send(update.Connect, password=password, version=update.version, extensions=update.extensions)
        updates = self.recv(timeout)
        if updates:
            if type(updates[0]) is not update.Connect:
                raise ConnectionFailed(update=update)
            for instance in updates:
                self.handle(instance)
        else:
            raise ConnectionFailed(message="Timeout")

    def disconnect(self):
        """Initiates a disconnect handshake if the client is connected."""
        if self.connected:
            self.send(update.Disconnect)

    def send(self, type, **args):
        """Sends a new update for the given type and set of arguments.

        See make_instance"""
        args['from'] = self.username
        args['clock'] = Client.clock()
        args['id'] = self.next_id()
        instance = update.make_instance(type, **args)
        self.send_raw(wire.to_string(instance.to_list()))
        return instance.id

    def recv(self, timeout=0):
        """Receive updates.

        Returns a list of update instances that were received.
        Timeout may be passed to specify a maximum amount of
        time to wait for updates. Note that this function may
        return even if there are more updates ready to be read.
        """
        strings = self.recv_raw(timeout)
        updates = []
        for string in strings:
            (update, _i) = read_update(string)
            if update != None:
                updates.append(update)
        return updates

    def handle(self, instance):
        """Handle the given update instance.

        This delivers it to the various handler functions.
        """
        for handler in self.handlers.get(instance.__class__, []):
            handler(self, instance)
        for handler in self.handlers[update.Update]:
            handler(self, instance)

    def loop(self):
        """Perform a basic connection loop of just receiving and handling updates."""
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
    """Parse an update from the string.

    Returns it and the position in the string after the update.

    If no update can be parsed or the item is not an update,
    None is returned instead of the update
    """
    (dat, i) = wire.from_string(string, i)
    if type(dat) == list and 0 < len(dat):
        instance = update.make_instance_plist(dat[0], dat[1:])
        return (instance, i)
    return (None, i)    
