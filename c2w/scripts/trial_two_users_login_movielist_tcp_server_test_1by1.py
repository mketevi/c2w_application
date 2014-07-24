#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import subprocess
from c2w.scripts._trial_generic import get_spec

FOR_SPECS = ['g14']
spec = get_spec(FOR_SPECS)


def main():
    trial_class = 'c2w.test.protocol.tcp_server_test.c2wTcpChatServerTestCase'
    cmdLine = ['trial',
               trial_class + '.test_two_users_login_movielist_tcp_server_test_1by1']
    try:
        retcode = subprocess.call(cmdLine)
    except KeyboardInterrupt:
        pass  # ignore CTRL-C

if __name__ == '__main__':
    main()