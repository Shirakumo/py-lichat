from .symbol import kw,li,make_package
from .wire import from_string,to_string
import os
import textwrap
import collections.abc
import inspect

version = '2.0'
extensions = set()
class_registry = {}

class LichatObject(collections.abc.MutableMapping):
    def __init__(self, **kwargs):
        if len(kwargs) > 0:
            raise ValueError(f"Unexpected field(s) reached LichatObject constructor; lichat class {to_string(self.__class__.__symbol__)!r} doesn't have field(s) {list(kwargs.keys())}.")

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

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"{key!r}")

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __delitem__(self, key):
        return delattr(self, key)

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

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

    nil_symbol = li('nil')
    
    def constructor(instance, **kwargs):
        for field in fields:
            if type(field) is str:
                field = field.lower()
            arg = kwargs.pop(field, None)
            if arg is None or arg is nil_symbol:
                setattr(instance, field, fields[field])
            else:
                setattr(instance, field, arg)
        super().__init__(**kwargs)

    def map_superclass(name):
        if inspect.isclass(name):
            return name
        if type(name) is str:
            name = li(name)
        return find_class(name)
    
    supers = tuple(map(map_superclass, supers))
                
    name = to_camelcase(symbol[1])
    __class__ = type(name, supers+(object,), {
        '__init__': constructor,
        '__symbol__': symbol
        })
    globals()[name] = __class__
    return register_class(symbol, __class__)

def parse_spec(*files):
    text = ""
    for file in files:
        with open(file) as f:
            text = text + f.read()
    
    classes = {}
    def parse_expr(expr):
        if expr[0][1] == 'define-package':
            make_package(expr[1])
        elif expr[0][1] == 'define-object':
            classes[expr[1]] = [
                set(expr[2]),
                expr[3:]
            ]
        elif expr[0][1] == 'define-object-extension':
            cls = classes[expr[1]]
            cls[0] = cls[0].union(set(expr[2]))
            cls[1] = cls[1] + expr[3:]
        elif expr[0][1] == 'define-extension':
            extensions.add(expr[1])
            for subexpr in expr[2:]:
                parse_expr(subexpr)

    start = 0
    while start < len(text):
        (expr, end) = from_string(text, start)
        start = end
        parse_expr(expr)

    for name in classes:
        cls = classes[name]
        slots = {}
        for slot in cls[1]:
            slots[slot[0][1]] = None

        supers = tuple(cls[0])
        if len(cls[0]) == 0:
            supers = (LichatObject, )

        defclass(name, supers, slots)

def load_base():
    dirname = os.path.dirname(__file__)
    parse_spec(os.path.join(dirname, 'spec/lichat.sexpr'),
               os.path.join(dirname, 'spec/shirakumo.sexpr'))

load_base()
