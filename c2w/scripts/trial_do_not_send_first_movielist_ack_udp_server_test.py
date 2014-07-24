#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import subprocess
import os
from c2w.scripts._trial_generic import get_spec

FOR_SPECS = ['g6', 'g14']
spec = get_spec(FOR_SPECS)

# decide if this script is relevant for the spec


def main():
    trial_class = 'c2w.test.protocol.udp_server_test.c2wUdpChatServerTestCase'
    cmdLine = ['trial',
               trial_class + '.test_do_not_send_first_movielist_ack_udp_server_test']
    try:
        retcode = subprocess.call(cmdLine)
    except KeyboardInterrupt:
        pass  # ignore CTRL-C

if __name__ == '__main__':
    main()
