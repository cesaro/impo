
import os
import sys
import time
import math
import networkx

import ptnet
import pes
import sat
import intervals

from util import *
from impo import *

def generate_ex () :
    n = ptnet.net.Net ()

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


def test1 () :
    n = ptnet.net.Net (True)
    n.read (sys.stdin, 'pnml')
    n.write (sys.stdout, 'pnml')

def test2 () :
    u = ptnet.unfolding.Unfolding (True)
    f = open ('dme2.cuf', 'r')
    u.read (f)
    print 'x' * 80
    print 'events'
    for e in u.events :
        print e
    print 'x' * 80
    print 'conditions'
    for c in u.conds :
        print c

    print 'x' * 80
    print 'dot'
    u.write (sys.stdout, 'dot')

def test3 () :
    u = ptnet.unfolding.Unfolding (True)
    f = open ('ex.cuf', 'r') # see generate_ex
    u.read (f)

    print 'bp'
    u.write (sys.stdout, 'dot')

    p = pes.bp_to_pes (u)

    print 'pes'
    print p
    for e in p.events :
        print ' e', e
    p.write (sys.stdout, 'dot')

    return

    print '0 < 1 ?', p.in_caus (p.events[0], p.events[1])
    print '1 < 0 ?', p.in_caus (p.events[1], p.events[0])
    print '0 < 5 ?', p.in_caus (p.events[0], p.events[5])
    print '0 < 6 ?', p.in_caus (p.events[0], p.events[6])
    print '1 < 5 ?', p.in_caus (p.events[1], p.events[5])
    print '2 < 5 ?', p.in_caus (p.events[2], p.events[5])
    print '5 < 2 ?', p.in_caus (p.events[5], p.events[2])
    print '3 < 2 ?', p.in_caus (p.events[3], p.events[2])
    print '4 < 0 ?', p.in_caus (p.events[4], p.events[0])
    print '1 < 4 ?', p.in_caus (p.events[1], p.events[4])
    print '7 < 4 ?', p.in_caus (p.events[7], p.events[4])

    print
    print p.__dict__['_PES__cau_rel']
    print

    print '0 # 0 ?', p.in_cfl (p.events[0], p.events[0])
    print '0 # 1 ?', p.in_cfl (p.events[0], p.events[1])
    print '1 # 0 ?', p.in_cfl (p.events[1], p.events[0])
    print '1 # 5 ?', p.in_cfl (p.events[1], p.events[5])
    print '1 # 2 ?', p.in_cfl (p.events[1], p.events[2])
    print '5 # 2 ?', p.in_cfl (p.events[5], p.events[2])
    print '5 # 4 ?', p.in_cfl (p.events[5], p.events[4])

    print
    print p.__dict__['_PES__cfl_rel']
    print

    print 'maximal events'
    print list (p.iter_maximal ())

def test4 () :
    n = ptnet.net.Net (True)
    f = open ('test.pnml', 'r')
    n.read (f, 'pnml')
    f = open ('test2.dot', 'w')
    n.write (f, 'dot')

def test5 () :
    u = ptnet.unfolding.Unfolding (True)
    #f = open ('ex.cuf', 'r') # see generate_ex
    f = open ('a22.unf.cuf', 'r')
    u.read (f)
    p = pes.bp_to_pes (u)

    print 'pes'
    print p
    for e in p.events :
        print ' e', e
    f = open ('out.dot', 'w') # see generate_ex
    p.write (f, 'dot')

    l = p.iter_max_confs ()
    for mx in l :
        print 'max conf:', mx
    print 'running assertions ............'
    for mx in l :
        # verify that every two maximal events of a config are not in conflict
        for e in mx :
            for ee in mx :
                assert not p.in_cfl (e, ee)
        # so causal closure is indeed a configuration, maximal?
        c = p.get_local_config (mx)
        assert len (c.enabled ()) == 0
    print 'done'

def test6 () :
    u = ptnet.unfolding.Unfolding (True)
    f = open ('ex.cuf', 'r')
    u.read (f)
    p = pes.bp_to_pes (u)

    e0 = p.events[0] # register
    e1 = p.events[1] # check
    e2 = p.events[2] # thoroughly
    e3 = p.events[3] # decide
    e4 = p.events[4] # reject
    e5 = p.events[5] # casually
    e7 = p.events[7] # repeat

    print 'x' * 80
    print 'test 1: empty comb'
    clauses = []
    comb = pes.Comb (p, clauses)
    l = comb.explore ()
    print 'test 1: l', l
    assert len (l) == 0

    print 'x' * 80
    print 'test 2: one event with empty spike'
    assert len (e1.cfl) == 0
    clauses = [list (e1.cfl)]
    comb = pes.Comb (p, clauses)
    l = comb.explore ()
    print 'test 2: l', l
    assert l == None

    print 'x' * 80
    print 'test 3: e2 has 1; e7 has 2; no solution'
    assert len (e2.cfl) == 1
    assert len (e7.cfl) == 2
    clauses = []
    clauses.append (list (e2.cfl))
    clauses.append (list (e7.cfl))
    comb = pes.Comb (p, clauses)
    l = comb.explore ()
    print 'test 3: l', l
    assert l == None

    print 'x' * 80
    print 'test 4: [e5, e1]  [e3]'
    clauses = []
    clauses.append ([e5, e1])
    clauses.append ([e3])
    comb = pes.Comb (p, clauses)
    l = comb.explore ()
    print 'test 4: l', l
    assert l == [e1, e3]

    print 'x' * 80
    print 'test 5: [e0, e1] [e5, e4]  [e7, e4]'
    clauses = []
    clauses.append ([e0, e1])
    clauses.append ([e5, e4])
    clauses.append ([e7, e4])
    comb = pes.Comb (p, clauses)
    l = comb.explore ()
    print 'test 5: l', l
    assert l == [e0, e4, e4]

def test7 () :
    g = networkx.Graph ()
    g.add_edge (1, 2)
    g.add_edge (3, 4)
    g.add_edge (3, 6)
    g.add_edge (4, 6)
    g.add_edge (5, 6)
    g.add_edge (6, 7)
    g.add_edge (6, 8)
    g.add_edge (7, 8)
    g.add_edge (8, 7)
    g.add_nodes_from (range (1, 12))

    print 'edges', g.edges ()
    print 'maximal cliques', list (networkx.find_cliques (g))
    # [[1, 2], [6, 8, 7], [6, 3, 4], [6, 5]]

def test8 () :
    #i = intervals.FloatInterval ((0,4))
    #i = intervals.FloatInterval ([0,4])
    i = intervals.FloatInterval.from_string ('[3,4]')
    #i = intervals.FloatInterval.open_closed (0,4)
    print i
    print i.lower
    print i.upper
    print i.lower_inc
    print i.upper_inc

    i.upper_inc = False
    i.lower = 2
    i.upper = float ('inf')
    print i
    print i.lower
    print i.upper
    print i.lower_inc
    print i.upper_inc
    print 3.999999999 in i
    print 'inf in i', float ('inf') in i
    print 'inf == upper', float ('inf') == i.upper

    a = intervals.FloatInterval ([0.0, float ('inf')])
    a.upper_inc = False
    i.lower = 0
    i.lower_inc = True
    print 'all', a
    print 'i', i
    print 'all == i', a == i

def test9 () :
    n = ptnet.tpn.Net ()
    p0 = n.place_add ('p0', 1)
    p1 = n.place_add ('p1')

    ival = intervals.FloatInterval ([0, float ('inf')])
    t = n.trans_add ('t-[0,inf]', ival)
    p0.post_add (t)
    p1.pre_add (t)

    ival = intervals.FloatInterval ([2, 4])
    t = n.trans_add ('t-[2,4]', ival)
    p0.post_add (t)
    p1.pre_add (t)

    ival = intervals.FloatInterval ([0, 7])
    ival.lower_inc = False
    t = n.trans_add ('t-(0,7]', ival)
    p0.post_add (t)
    p1.pre_add (t)

    ival = intervals.FloatInterval ([1, 2])
    ival.upper_inc = False
    t = n.trans_add ('t-[1,2)', ival)
    p0.post_add (t)
    p1.pre_add (t)

    ival = intervals.FloatInterval ((1, 2))
    t = n.trans_add ('t-(1,2)', ival)
    p0.post_add (t)
    p1.pre_add (t)

    ival = intervals.FloatInterval ([1, float('inf')])
    t = n.trans_add ('t-[10,inf)', ival)
    p0.post_add (t)
    p1.pre_add (t)

    n.write (sys.stdout, 'pnml')
    n.write (sys.stdout, 'pt1')

def test10 () :
    n = ptnet.tpn.Net (True)
    f = open ('test.pnml', 'r')
    n.read (f, 'pnml')
    f = open ('test2.dot', 'w')
    n.write (f, 'dot')

def test11 () :
    print size_human (100)
    print size_human (1000)
    print size_human (2000)
    print size_human (3000)
    print size_human (4000)
    print size_human (8000)
    print size_human (10 * 1024 + 600)
    print size_human (1023 * 1024 + 600)
    print size_human (1024 * 1024 * 2.5)
    print size_human (1024 * 1024 * 600)
    print size_human (1024 * 1024 * 1026)
    print size_human (1024 * 1024 * 8026)
    print size_human (1024 * 1024 * 8026 * 1024)

def test12 () :
    u = ptnet.unfolding.Unfolding (True)
    #f = open ('ex.cuf', 'r') # see generate_ex
    f = open ('ex.cuf', 'r')
    u.read (f)
    p = pes.bp_to_pes (u)

    print 'pes'
    print p
    for e in p.events :
        print ' e', e
    f = open ('out.dot', 'w') # see generate_ex
    p.write (sys.stdout, 'dot')
    p.write (open ('ex.dot', 'w'), 'dot')

    p2 = pes.pes_to_ct (p)

    p2.write (open ('out.dot', 'w'), 'dot')
    p2.write (sys.stdout, 'dot')


# vi:ts=4:sw=4:et:
