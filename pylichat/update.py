from .symbol import kw,li

version = '2.0'

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

def register_class(symbol, clazz):
    class_registry[symbol] = clazz
    return clazz

def find_class(symbol):
    return class_registry.get(symbol, None)

def make_instance(symbol, **initargs):
    clazz = find_class(symbol)
    if clazz == None:
        return None
    return clazz(**initargs)

def make_instance_plist(symbol, initargs):
    kwargs = {}
    for k,v in zip(*[iter(initargs)]*2):
        if type(k) is tuple and k[0] == 'KEYWORD':
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
                instance[field] = fields[field]
            else:
                instance[field] = arg
                
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
defclass('message', (ChannelUpdate, TextUpdate))
defclass('users', (ChannelUpdate,), {
    'users': [] })
defclass('channels', (), {
    'channels': []})
defclass('user-info', (TargetUpdate,), {
    'registered': None,
    'connections': None })
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
defclass('pause', (ChannelUpdate,), {
    'by': 0 })
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
defclass('clock-skewed', (UpdateFailure,))
