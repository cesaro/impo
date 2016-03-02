#!/usr/bin/env python

import sys
import ptnet.unfolding

if __name__ == '__main__' :
    u = ptnet.unfolding.Unfolding (True)
    u.read (sys.stdin, 'cuf')
    u.write (sys.stdout, 'pnml')

# vi:ts=4:sw=4:et:
