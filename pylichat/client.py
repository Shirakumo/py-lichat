import .symbol
import .update
import time

class Client:
    def __init__(self, username):
        self.username = username
        self.servername = None
        self.id = 0

    def clock():
        int(time.time()) + 2208988800

    def next_id():
        self.id = self.id+1
        return self.id

    def s(self, type, **args):
        args['from'] = self.username
        args['clock'] = self.clock()
        args['id'] = self.next_id()
        instance = update.make_instance(symbol.li(type), **args)
        return self.send_raw(wire.to_string(instance.to_list()))

    def send_raw(string):
        return true
