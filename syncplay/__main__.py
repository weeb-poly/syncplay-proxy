#!/usr/bin/env python3

import logging

from . import ep_proxy

def main():
    logging.basicConfig(level=logging.INFO)
    ep_proxy.main()

if __name__ == '__main__':
    main()
