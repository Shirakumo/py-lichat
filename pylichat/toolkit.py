import collections.abc

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
