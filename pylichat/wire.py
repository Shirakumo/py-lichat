from functools import singledispatch
from .symbol import intern
import decimal

float_ctx = decimal.Context()
float_ctx.prec = 20

@singledispatch
def to_string(thing):
    raise ValueError("Don't know what to do with {0}.".format(thing))

def strchar(x):
    if x == '"': return '\\"'
    elif x == '\0': return ''
    else: return x

@to_string.register
def _(thing: str):
    return '"'+''.join([strchar(x) for x in thing])+'"'

@to_string.register
def _(thing: list):
    return '('+' '.join([to_string(x) for x in thing])+')'

@to_string.register
def _(thing: int):
    return format(thing)

@to_string.register
def _(thing: float):
    return format(float_ctx.create_decimal(repr(thing)), 'f')

@to_string.register
def _(thing: tuple):
    if thing[0] == 'keyword':
        return ':'+thing[1]
    elif thing[0] == 'lichat-protocol':
        return thing[1]
    else:
        return thing[0]+':'+thing[1]

@to_string.register
def _(thing: bool):
    if thing:
        return 'T'
    else:
        return 'NIL'

@to_string.register
def _(thing: type(None)):
    return 'NIL'

def consume_whitespace(string, i, end):
    while i<end and string[i] in '\u0009\u000A\u000B\u000C\u000D\u0020':
        i = i+1
    return i

def read_list(string, i, end):
    if i<end and string[i] == '(':
        i = i+1
        items = []
        while i<end and string[i] != ')' and string[i] != '\0':
            (item, ni) = from_string(string, i)
            items.append(item)
            i = consume_whitespace(string, ni, end)
        if i<end and string[i] == ')':
            i = i+1
        return (items, i)

def read_string(string, i, end):
    if i<end and string[i] == '"':
        i = i+1
        result = ''
        while i<end and string[i] != '"' and string[i] != '\0':
            if string[i] == '\\':
                i = i+1
            result = result+string[i]
            i = i+1
        if i<end and string[i] == '"':
            i = i+1
        return (result, i)

def read_number_part(string, i, end):
    decimal = 0
    while i<end and string[i] in '0123456789':
        decimal = decimal*10 + (ord(string[i])-48)
        i = i+1
    return (decimal, i)

def read_number(string, i, end):
    if i<end and string[i] in '0123456789.':
        (decimal, i) = read_number_part(string, i, end)
        if i<end and string[i] == '.':
            i = i+1
            (fract, ni) = read_number_part(string, i, end)
            num = decimal + float(fract) / (10.0 ** (ni-i))
            return (num, ni)
        return (decimal, i)

def read_token(string, i, end):
    token = ''
    while i<end and string[i] not in ': ".()':
        if string[i] == '\\':
            i = i+1
        token = token+string[i]
        i = i+1
    return (token, i)

def read_symbol(string, i, end):
    name = ''
    (package, i) = read_token(string, i, end)
    if i<end and string[i] == ':':
        i = i+1
        if package == '':
            package = 'keyword'
        (name, i) = read_token(string, i, end)
        return (intern(name, package), i)
    else:
        return (intern(package), i)

def from_string(string, i=0, end=-1):
    if end < 0: end = len(string)
    i = consume_whitespace(string, i, end)
    return (read_list(string, i, end)
            or read_string(string, i, end)
            or read_number(string, i, end)
            or read_symbol(string, i, end))
