from .symbol import kw,li
import textwrap

version = '2.0'
extensions = ['shirakumo-data', 'shirakumo-backfill', 'shirakumo-emotes', 'shirakumo-edit', 'shirakumo-channel-info', 'shirakumo-quiet', 'shirakumo-pause', 'shirakumo-server-management', 'shirakumo-ip', 'shirakumo-channel-trees']

class_registry={}

class Update:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.clock = kwargs.get('clock', None)
        setattr(self, 'from', kwargs.get('from', None))

    def to_list(self):
        plist = []
        for key in self.__dict__.keys():
            val = self.__dict__[key]
            if val != None:
                plist.append(kw(key))
                plist.append(val)
        return [ self.__symbol__ ] + plist

    def unix_clock(self):
        return self.clock - 2208988800

    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default

    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __repr__(self):
        return (f"{self.__class__.__qualname__}("
                + ", ".join(f"{k}={self[k]!r}" for k in self.__dict__)
                + ")")

    def __str__(self):
        return (f"{self.__class__.__qualname__}("
                + ", ".join(f"{k}={textwrap.shorten(str(self[k]), width=74)}" for k in self.__dict__)
                + ")")

def register_class(symbol, clazz):
    class_registry[symbol] = clazz
    return clazz

def find_class(symbol):
    return class_registry.get(symbol, None)

def make_instance(clazz, **initargs):
    if type(clazz) == tuple:
        clazz = find_class(clazz)
    if clazz == None:
        return None
    return clazz(**initargs)

def make_instance_plist(symbol, initargs):
    kwargs = {}
    for k,v in zip(*[iter(initargs)]*2):
        if type(k) is tuple and k[0] == 'keyword':
            kwargs[k[1].lower()] = v
        else:
            kwargs[k] = v
    return make_instance(symbol, **kwargs)

def to_camelcase(name):
    return ''.join(x.title() for x in name.split('-'))

def defclass(symbol, supers=(), fields={}):
    if type(symbol) is str:
        symbol = li(symbol)
    __class__ = None
    
    def constructor(instance, **kwargs):
        super().__init__(**kwargs)
        for field in fields:
            if type(field) is str:
                field = field.lower()
            arg = kwargs.get(field, None)
            if arg == None:
                setattr(instance, field, fields[field])
            else:
                setattr(instance, field, arg)
                
    name = to_camelcase(symbol[1])
    __class__ = type(name, supers+(Update, object), {
        '__init__': constructor,
        '__symbol__': symbol
        })
    globals()[name] = __class__
    return register_class(symbol, __class__)

defclass('ping')
defclass('pong')
defclass('connect', (), {
    'password': None,
    'version': version,
    'extensions': [] })
defclass('disconnect')
defclass('register')
defclass('channel-update', (), {
    'channel': None })
defclass('target-update', (), {
    'target': None })
defclass('text-update', (), {
    'text': None })
defclass('join', (ChannelUpdate,))
defclass('leave', (ChannelUpdate,))
defclass('create', (ChannelUpdate,))
defclass('kick', (ChannelUpdate, TargetUpdate))
defclass('pull', (ChannelUpdate, TargetUpdate))
defclass('permissions', (ChannelUpdate,), {
    'permissions': [] })
defclass('grant', (ChannelUpdate, TargetUpdate), {
    'update': None})
defclass('deny', (ChannelUpdate, TargetUpdate), {
    'update': None})
defclass('capabilities', (ChannelUpdate,), {
    'permitted': None})
defclass('message', (ChannelUpdate, TextUpdate))
defclass('edit', (ChannelUpdate, TextUpdate))
defclass('users', (ChannelUpdate,), {
    'users': [] })
defclass('channels', (ChannelUpdate,), {
    'channels': []})
defclass('user-info', (TargetUpdate,), {
    'registered': None,
    'connections': None,
    'info': None })
defclass('server-info', (TargetUpdate,), {
    'attributes': None,
    'connections': None})
defclass('backfill', (ChannelUpdate,))
defclass('data', (ChannelUpdate,), {
    'content-type': None,
    'filename': None,
    'payload': None })
defclass('emotes', (), {
    'names': [] })
defclass('emote', (), {
    'content-type': None,
    'name': None,
    'payload': None })
defclass('channel-info', (ChannelUpdate,), {
    'keys': True })
defclass('set-channel-info', (ChannelUpdate, TextUpdate), {
    'key': None })
defclass('set-user-info', (TextUpdate,), {
    'key': None })
defclass('pause', (ChannelUpdate,), {
    'by': 0 })
defclass('kill', (TargetUpdate,))
defclass('destroy', (ChannelUpdate,))
defclass('ban', (TargetUpdate,))
defclass('unban', (TargetUpdate,))
defclass('ip-ban', (), {
    'ip': None,
    'mask': None})
defclass('ip-unban', (), {
    'ip': None,
    'mask': None})
defclass('quiet', (ChannelUpdate, TargetUpdate))
defclass('unquiet', (ChannelUpdate, TargetUpdate))
defclass('failure', (TextUpdate,))
defclass('malformed-update', (Failure,))
defclass('update-too-long', (Failure,))
defclass('connection-unstable', (Failure,))
defclass('too-many-connections', (Failure,))
defclass('update-failure', (Failure,), {
    'update-id': None })
defclass('invalid-update', (UpdateFailure,))
defclass('username-mismatch', (UpdateFailure,))
defclass('incompatible-version', (UpdateFailure,), {
    'compatible-versions': [] })
defclass('invalid-password', (UpdateFailure,))
defclass('no-such-profile', (UpdateFailure,))
defclass('username-taken', (UpdateFailure,))
defclass('no-such-channel', (UpdateFailure,))
defclass('already-in-channel', (UpdateFailure,))
defclass('not-in-channel', (UpdateFailure,))
defclass('channelname-taken', (UpdateFailure,))
defclass('bad-name', (UpdateFailure,))
defclass('insufficient-permissions', (UpdateFailure,))
defclass('no-such-user', (UpdateFailure,))
defclass('too-many-updates', (UpdateFailure,))
defclass('bad-content-type', (UpdateFailure,), {
    'allowed-content-types': []})
defclass('no-such-channel-info', (UpdateFailure,), {
    'key': None })
defclass('malformed-channel-info', (UpdateFailure,))
defclass('no-such-user-info', (UpdateFailure,), {
    'key': None })
defclass('malformed-user-info', (UpdateFailure,))
defclass('clock-skewed', (UpdateFailure,))
defclass('no-such-parent-channel', (UpdateFailure,))
