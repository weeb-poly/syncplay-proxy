import os
import logging

from twisted.internet.endpoints import TCP4ServerEndpoint, TCP6ServerEndpoint

from syncplay.server import SyncplayProxyWSFactory
from syncplay.server import SyncplayProxyTCPFactory

from twisted.internet import reactor

# from autobahn.twisted.choosereactor import install_reactor

# reactor = install_reactor()


def setupFactory(factory, port: int, type: str) -> None:
    endpoint6 = TCP6ServerEndpoint(reactor, port)

    def failed6(e):
        logging.debug(e)
        logging.error(f"IPv6 listening failed ({type}).")

    endpoint6.listen(factory).addErrback(failed6)

    endpoint4 = TCP4ServerEndpoint(reactor, port)

    def failed4(e):
        logging.debug(e)
        logging.error(f"IPv4 listening failed ({type}).")

    endpoint4.listen(factory).addErrback(failed4)


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
        setupFactory(tcp_factory, int(tcport), "TCP")

    if wsport is not None:
        ws_factory = SyncplayProxyWSFactory(
            wsport,
            host
        )
        setupFactory(ws_factory, int(wsport), "WS")

    reactor.run()


if __name__ == "__main__":
    main()
