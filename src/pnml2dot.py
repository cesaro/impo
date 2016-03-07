#!/usr/bin/env python

import sys
import ptnet

if __name__ == '__main__' :
    n = ptnet.tpn.Net (True) # in PNML, every P/T net is a TPN ;)
    n.read (sys.stdin, 'pnml')
    n.write (sys.stdout, 'dot')

# vi:ts=4:sw=4:et:
