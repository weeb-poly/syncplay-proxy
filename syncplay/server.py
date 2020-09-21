import argparse
import codecs
import hashlib
import os
import time
from string import Template
import logging

from twisted.enterprise import adbapi
from twisted.internet import task, reactor
from twisted.internet.protocol import Factory

try:
    from OpenSSL import crypto
    from OpenSSL.SSL import TLSv1_2_METHOD
    from twisted.internet import ssl
except:
    pass

import syncplay
from syncplay import constants
from syncplay.protocols import SyncProxyServerProtocol


class SyncProxyFactory(Factory):
    port: str
    host: str
    tlscertPath: str
    serverAcceptsTLS: bool
    _TLSattempts: int

    def __init__(self, port: str = '', host: str = '', tlsCertPath = None):
        self.port = port

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

    def buildProtocol(self, addr):
        return SyncProxyServerProtocol(self)

    def _allowTLSconnections(self, path: str) -> None:
        try:
            privKey = open(path+'/privkey.pem', 'rt').read()
            certif = open(path+'/cert.pem', 'rt').read()
            chain = open(path+'/chain.pem', 'rt').read()

            self.lastEditCertTime = os.path.getmtime(path+'/cert.pem')

            privKeyPySSL = crypto.load_privatekey(crypto.FILETYPE_PEM, privKey)
            certifPySSL = crypto.load_certificate(crypto.FILETYPE_PEM, certif)
            chainPySSL = [crypto.load_certificate(crypto.FILETYPE_PEM, chain)]

            cipherListString = "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"\
                               "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"\
                               "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
            accCiphers = ssl.AcceptableCiphers.fromOpenSSLCipherString(cipherListString)

            try:
                contextFactory = ssl.CertificateOptions(privateKey=privKeyPySSL, certificate=certifPySSL,
                                                        extraCertChain=chainPySSL, acceptableCiphers=accCiphers,
                                                        raiseMinimumTo=ssl.TLSVersion.TLSv1_2)
            except AttributeError:
                contextFactory = ssl.CertificateOptions(privateKey=privKeyPySSL, certificate=certifPySSL,
                                                        extraCertChain=chainPySSL, acceptableCiphers=accCiphers,
                                                        method=TLSv1_2_METHOD)

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
            outTime = os.path.getmtime(self.certPath+'/cert.pem')
        except:
            outTime = None
        return outTime

    def updateTLSContextFactory(self) -> None:
        self._allowTLSconnections(self.certPath)
        self._TLSattempts += 1
        if self._TLSattempts < constants.TLS_CERT_ROTATION_MAX_RETRIES:
            self.serverAcceptsTLS = True

