import argparse
import codecs
import hashlib
import os
import time
from string import Template
import logging

import pem

from twisted.internet import task, reactor
from twisted.internet.protocol import ServerFactory

try:
    from OpenSSL.SSL import TLSv1_2_METHOD
    from twisted.internet import ssl
except:
    pass

import syncplay
from syncplay import constants
from syncplay.protocols import SyncplayTCPServerProtocol
from syncplay.protocols import SyncplayWSServerProtocol

from autobahn.twisted.websocket import WebSocketServerFactory


class SyncplayProxyWSFactory(WebSocketServerFactory):
    port: str
    host: str

    def __init__(self, port: str = '', host: str = ''):
        self.port = port

        host_name, host_port = host.split(":", 1)
        self.host_name = host_name
        self.host_port = int(host_port)

    def buildProtocol(self, _addr):
        return SyncplayWSServerProtocol(self)


class SyncplayProxyTCPFactory(ServerFactory):
    port: int
    host: str
    tlscertPath: str
    serverAcceptsTLS: bool
    _TLSattempts: int

    def __init__(self, port: str = '', host: str = '', tlsCertPath = None):
        self.port = int(port)

        host_name, host_port = host.split(":", 1)
        self.host_name = host_name
        self.host_port = int(host_port)

        self.certPath = tlsCertPath
        self.serverAcceptsTLS = False
        self._TLSattempts = 0
        if self.certPath is not None:
            self._allowTLSconnections(self.certPath)
        else:
            self.options = None

    def buildProtocol(self, _addr):
        return SyncplayTCPServerProtocol(self)

    def _allowTLSconnections(self, path: str) -> None:
        try:
            privKeyPath = path+'/privkey.pem'
            chainPath = path+'/fullchain.pem'

            self.lastEditCertTime = os.path.getmtime(chainPath)

            cipherListString = "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"\
                               "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"\
                               "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
            accCiphers = ssl.AcceptableCiphers.fromOpenSSLCipherString(cipherListString)

            try:
                contextFactory = pem.twisted.certificateOptionsFromFiles(
                    privKeyPath,
                    chainPath,
                    acceptableCiphers=accCiphers,
                    raiseMinimumTo=ssl.TLSVersion.TLSv1_2
                )
            except AttributeError:
                contextFactory = pem.twisted.certificateOptionsFromFiles(
                    privKeyPath,
                    chainPath,
                    acceptableCiphers=accCiphers,
                    method=TLSv1_2_METHOD
                )

            self.options = contextFactory
            self.serverAcceptsTLS = True
            self._TLSattempts = 0
            logging.info("TLS support is enabled.")
        except Exception:
            self.options = None
            self.serverAcceptsTLS = False
            self.lastEditCertTime = None
            logging.exception("Error while loading the TLS certificates.")
            logging.info("TLS support is not enabled.")

    def checkLastEditCertTime(self):
        try:
            outTime = os.path.getmtime(self.certPath+'/fullchain.pem')
        except:
            outTime = None
        return outTime

    def updateTLSContextFactory(self) -> None:
        self._allowTLSconnections(self.certPath)
        self._TLSattempts += 1
        if self._TLSattempts < constants.TLS_CERT_ROTATION_MAX_RETRIES:
            self.serverAcceptsTLS = True

