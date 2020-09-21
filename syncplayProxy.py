#!/usr/bin/env python3

import logging

from syncplay import proxy

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    proxy.main()
