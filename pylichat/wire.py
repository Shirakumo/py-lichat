from functools import singledispatch
from .symbol import intern
import decimal

float_ctx = decimal.Context()
float_ctx.prec = 20

@singledispatch
def to_string(thing):
    raise ValueError("Don't know what to do with this.")

@to_string.register
def _(thing: str):
    '"'+''.join(['\\"' if x == '"' else x for x in str])+'"'

@to_string.register
def _(thing: list):
    '('+' '.join([to_string(x) for x in thing])+')'

@to_string.register
def _(thing: Decimal):
    return format(thing)

@to_string.register
def _(thing: float):
    return format(float_ctx.create_decimal(repr(thing)), 'f')

@to_string.register
def _(thing: tuple):
    if tuple[0] == 'keyword':
        return ':'+tuple[1]
    else if tuple[0] == 'lichat-protocol':
        return tuple[1]
    else
        return tuple[0]+':'+tuple[1]

@to_string.register
def _(thing: bool):
    if thing:
        return 'T'
    else:
        return 'NIL'

@to_string.register
def _(thing: NoneType):
    return 'NIL'

def consume_whitespace(string, i):
    while string[i] in '\u0009\u000A\u000B\u000C\u000D\u0020':
        i = i+1
    return i

def read_list(string, i=0):
    if string[i] == '(':
        i = i+1
        items = []
        while string[i] != ')' and string[i] != '\0':
            (item, ni) = from_string(string, i)
            i = consume_whitespace(string, ni)
            items.append(item)
        return (items, i)

def read_string(string, i=0):
    if string[i] == '"':
        i = i+1
        result = ''
        while string[i] != '"' and string[i] != '\0':
            if string[i] == '\\':
                i = i+1
            result = result+string[i]
            i = i+1
        return (result, i)

def read_number_part(string, i=0):
    decimal = 0
    while string[i] in '0123456789':
        decimal = decimal*10 + (ord(string[i])-48)
        i = i+1
    return (decimal, i)

def read_number(string, i=0):
    if string[i] in '0123456789.':
        (decimal, i) = read_number_part(string, i)
        if string[i] == '.':
            (fract, ni) = read_number_part(string, i)
            num = decimal + fract / (10.0 ** (ni-i))
            return (num, ni)
        return (decimal, i)

def read_symbol(string, i=0):
    name = ''
    (package, i) = read_token(string, i)
    if string[i] == ':':
        if package == '':
            package = 'keyword'
        else:
            (name, ni) = read_token(string, i)
            i = ni
    else:
        name = package
        package = 'lichat-protocol'
    return (find_symbol(name, package), i)

def from_string(string, i=0):
    i = consume_whitespace(string, i)
    read_list(string, i)
    or read_string(string, i)
    or read_number(string, i)
    or read_symbol(string, i)
