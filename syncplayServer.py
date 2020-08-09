#!/usr/bin/env python3
# coding:utf8

import logging

from syncplay import ep_server

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ep_server.main()
