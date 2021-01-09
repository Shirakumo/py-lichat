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
