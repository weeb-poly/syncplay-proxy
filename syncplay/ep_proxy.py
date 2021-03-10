import os
import logging

from twisted.internet.endpoints import TCP4ServerEndpoint, SSL4ServerEndpoint

from syncplay.server import SyncplayProxyWSFactory
from syncplay.server import SyncplayProxyTCPFactory

from twisted.internet import reactor

# from autobahn.twisted.choosereactor import install_reactor
# reactor = install_reactor()


def setupTCPFactory(factory, port: int) -> None:
    connType = "TCP"

    endpoint4 = TCP4ServerEndpoint(reactor, port)
    setupEndpoint(endpoint4, factory, "IPv4", connType)


def setupWSFactory(factory, port: int) -> None:
    connType = "WS"

    if factory.options is not None:
        endpoint4 = SSL4ServerEndpoint(reactor, port, factory.options)
    else:
        endpoint4 = TCP4ServerEndpoint(reactor, port)
    setupEndpoint(endpoint4, factory, "IPv4", connType)


def setupEndpoint(endpoint, factory, addrType: str, connType: str) -> None:
    def listenFailed(e):
        logging.exception(e)
        logging.exception(f"{addrType} listening failed ({connType}).")
    endpoint.listen(factory).addErrback(listenFailed)


def main():
    tcport = os.environ.get('SYNCPLAY_TCP_PORT', None)
    wsport = os.environ.get('SYNCPLAY_WS_PORT', None)
    host = os.environ.get('SYNCPLAY_HOST', 'syncplay.pl:8997')
    tls = os.environ.get('SYNCPLAY_TLS_PATH')

    if tcport is not None:
        tcp_factory = SyncplayProxyTCPFactory(
            tcport,
            host,
            tls
        )
        setupTCPFactory(tcp_factory, int(tcport))

    if wsport is not None:
        ws_factory = SyncplayProxyWSFactory(
            wsport,
            host,
            tls
        )
        setupWSFactory(ws_factory, int(wsport))

    reactor.run()


if __name__ == "__main__":
    main()
