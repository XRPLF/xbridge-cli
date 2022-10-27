import threading

from xrpl.clients import JsonRpcClient
from xrpl.models import GenericRequest


class SetInterval:
    def __init__(self, func, sec):
        def func_wrapper():
            self.t = threading.Timer(sec, func_wrapper)
            self.t.start()
            func()

        self.t = threading.Timer(sec, func_wrapper)
        self.t.start()

    def cancel(self):
        self.t.cancel()


def close_ledgers():
    JsonRpcClient("http://localhost:5005").request(
        GenericRequest(method="ledger_accept")
    )
    JsonRpcClient("http://localhost:5006").request(
        GenericRequest(method="ledger_accept")
    )
