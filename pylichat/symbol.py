package_table={}

def find_package(name):
    return package_table.get(name.lower(), None)

def make_package(name, symbols=[]):
    name = name.lower()
    index = find_package(name)
    if index == None:
        index = {}
        package_table[name] = index
    for symbol in symbols:
        symbol = symbol.lower()
        if index.get(symbol, None) == None:
            index[symbol] = (name, symbol)
    return index

def delete_package(name):
    del package_table[name.lower()]

def find_symbol(name, package='lichat-protocol'):
    index = find_package(package.lower())
    if index == None:
        raise ValueError('No such package')
    return index.get(name.lower(), None)

def intern(name, package='lichat-protocol'):
    name = name.lower()
    package = package.lower()
    index = find_package(package)
    if index == None:
        return None
    existing = index.get(name, None)
    if existing == None:
        existing = (package, name)
        index[name] = existing
    return existing

def unintern(symbol):
    (package, name) = symbol
    index = find_package(package)
    del index[name]
    return None

def kw(name):
    return intern(name, 'keyword')

def li(name):
    return intern(name, 'lichat-protocol')

make_package('lichat-protocol')
make_package('keyword')
