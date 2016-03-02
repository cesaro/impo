#!/usr/bin/env python

import ptnet
import sys

def generate () :
    n = ptnet.Net ()

    t1 = n.trans_add ("register")
    t2 = n.trans_add ("repeat")
    t3 = n.trans_add ("check")
    t4 = n.trans_add ("throughly")
    t5 = n.trans_add ("casually")
    t6 = n.trans_add ("decide")
    t7 = n.trans_add ("reject")
    t8 = n.trans_add ("compensation")

    p = []
    for i in range (7) :
        p.append (n.place_add ("p%d" % i))

    t1.pre_add (p[0])
    t1.post_add (p[1])
    t1.post_add (p[2])

    t2.pre_add (p[5])
    t2.post_add (p[1])
    t2.post_add (p[2])

    t3.pre_add (p[1])
    t3.post_add (p[3])

    t4.pre_add (p[2])
    t4.post_add (p[4])
    t5.pre_add (p[2])
    t5.post_add (p[4])

    t6.pre_add (p[3])
    t6.pre_add (p[4])
    t6.post_add (p[5])


    t7.pre_add (p[5])
    t7.post_add (p[6])
    t8.pre_add (p[5])
    t8.post_add (p[6])

    n.m0[p[0]] = 1
    n.write (sys.stdout, 'pnml')

if __name__ == '__main__' :
    generate ()


# vi:ts=4:sw=4:et:
