#!/usr/bin/env python2

#
# Generates a Time Petri Net of the Fischer algorithm for NUM_PROCESSES
# processes, choosing a quite high delay for the the pause transition, so mutual
# exclusion is surely guaranteed
#
# https://www2.informatik.hu-berlin.de/~hs/Aktivitaeten/2011_Vino/Talks/Morning/11_Tom-Davies_Fischers-Algorithm.pdf
# Slide 20
#

import intervals
import ptnet
import sys

def nameit (s, it) :
    if it != 0 :
        return s + "_it%d" % it
    else :
        return s

def mk_fischer_iter (n, numproc, it, startp, endp, idp) :

    # map from (Process x Location) to Place
    loc = {}

    # At loc0: if id=0, then move to loc1
    for i in range (1, numproc + 1) :
        dly = intervals.FloatInterval ([0, 1])
        t = n.trans_add (nameit ('p%d_if_id=0' % i, it), dly)
        p = n.place_add (nameit ('p%d_l1' % i, it))
        loc[i, 1] = p
        t.pre_add (startp[i])
        t.post_add (p)
        t.cont_add (idp[0]) # place 'id=0'

    # At loc1: set id=i and move to loc2
    for i in range (1, numproc + 1) :
        p = n.place_add (nameit ('p%d_l2' % i, it))
        loc[i, 2] = p
        for j in range (numproc + 1) : # including id=0
            dly = intervals.FloatInterval ([0, 1])
            t = n.trans_add (nameit ('p%d_setid%d' % (i, j), it), dly)
            t.pre_add (loc[i, 1])
            t.pre_add (idp[j])
            t.post_add (p)
            t.post_add (idp[i])

    # At loc2: pause and move to loc3
    for i in range (1, numproc + 1) :
        p = n.place_add (nameit ('p%d_l3' % i, it))
        loc[i, 3] = p
        dly = intervals.FloatInterval ([10, 10])
        t = n.trans_add (nameit ('p%d_pause' % i, it), dly)
        t.pre_add (loc[i,2])
        t.post_add (p)

    # At loc3: if id=i then move to loc4; else move to l0
    for i in range (1, numproc + 1) :
        p = n.place_add (nameit ('p%d_l4' % i, it))
        loc[i, 4] = p
        for j in range (numproc + 1) : # including id=0
            dly = intervals.FloatInterval ([0, 0])
            if i == j :
                t = n.trans_add (nameit ('p%d_ifideq' % i, it), dly)
                t.post_add (p)
            else :
                t = n.trans_add (nameit ('p%d_ifidne%d' % (i, j), it), dly)
                t.post_add (startp[i])
            t.cont_add (idp[j])
            t.pre_add (loc[i, 3])

    # loc4 is the critical section :)

    # at loc4: set id=0 and move to loc5 (end)
    for i in range (1, numproc + 1) :
        for j in range (numproc + 1) : # including id=0
            dly = intervals.FloatInterval ([0, 3])
            t = n.trans_add (nameit ('p%d_exit%d' % (i, j), it), dly)
            t.pre_add (loc[i, 4])
            t.pre_add (idp[j])
            t.post_add (endp[i])
            t.post_add (idp[0])

def mk_fischer (numproc, numit) :

    # create numproc initial places
    n = ptnet.tpn.Net ()
    startp = [None] # unused first idx
    for i in range (1, numproc + 1) :
        startp.append (n.place_add (nameit ('p%d_l0' % i, 0), 1))

    # id places, one per process + 1, only 'id=0' is initially marked
    idp = []
    for i in range (numproc + 1) :
        idp.append (n.place_add ('id=%d' % i, 1 if i == 0 else 0))

    # for each iteration, create the end places and build an iteration
    for it in range (numit) :
        endp = [None] # unused first idx
        for i in range (1, numproc + 1) :
            endp.append (n.place_add (nameit ('p%d_l5' % i, it)))
        mk_fischer_iter (n, numproc, it, startp, endp, idp)
        startp = endp

    return n

def usage () :
    #sys.stderr.write ('usage: mk_fischer.py NUM_PROCESSES NUM_ITERS\n')
    sys.stderr.write ('usage: mk_fischer.py NUM_PROCESSES\n')
    sys.exit (1)

def main () :
    try :
        numproc = int (sys.argv[1])
        #numiter = int (sys.argv[2])
    except :
        usage ()

    numiter = 1
    n = mk_fischer (numproc, numiter)
    n.write (sys.stdout, 'pnml')

if __name__ == '__main__' :
    main ()
    sys.exit (0)
