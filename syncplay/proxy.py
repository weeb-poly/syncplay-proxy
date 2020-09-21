import os
import sys
import logging

from twisted.internet.task import react
from twisted.internet.defer import ensureDeferred, Deferred

from twisted.internet.endpoints import TCP4ServerEndpoint, TCP6ServerEndpoint
from twisted.internet.error import CannotListenError

from syncplay.server import SyncProxyFactory


async def _main(reactor):
    port = os.environ.get('SYNCPLAY_PORT', '8995')
    host = os.environ.get('SYNCPLAY_HOST', 'syncplay.weebpoly.ml:8996')
    tls = os.environ.get('SYNCPLAY_TLS_PATH')
    factory = SyncProxyFactory(
        port,
        host,
        tls
    )

    endpoint6 = TCP6ServerEndpoint(reactor, int(port))
    listening6 = False
    try:
        await endpoint6.listen(factory)
    except CannotListenError as e:
        logging.debug(e.value)
        logging.error("IPv6 listening failed.")
    else:
        listening6 = True

    endpoint4 = TCP4ServerEndpoint(reactor, int(port))
    listening4 = False
    try:
        await endpoint4.listen(factory)
    except CannotListenError as e:
        if not listening6:
            logging.debug(e.value)
            logging.error("IPv4 listening failed.")
    else:
        listening4 = True

    if listening6 or listening4:
        # reactor.run()
        await Deferred()
    else:
        logging.error("Unable to listen using either IPv4 and IPv6 protocols. Quitting the server now.")
        sys.exit()


def main():
    return react(
        lambda reactor: ensureDeferred(
            _main(reactor)
        )
    )


if __name__ == "__main__":
    main()
