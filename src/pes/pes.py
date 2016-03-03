
import sys

from configuration import *
from maxconfs import *

def bp_to_pes (bp) :

    bp2pes = {}
    p = PES ()

    # first pass, map all events
    for e in bp.events :
        #print 'e', e
        bp2pes[e] = p.add_event (e.label, [], [])

    # second panss, set causality and conflicts
    for e,ee in bp2pes.items () :
        for c in e.pre :
            for epre in c.pre :
                ee.pre_add (bp2pes[epre])
            for epost in c.post :
                if epost != e :
                    ee.cfl_add (bp2pes[epost])

    p.update_minimal ()
    return p

class Event :
    def __init__ (self, nr, label) :
        self.pre = set ()
        self.post = set ()
        self.cfl = set ()
        self.label = label
        self.nr = nr
        self.m = 0
        self.m_cc = 0 # for PES.is_{cau,cfl}
    
    def pre_add (self, e) :
        if e in self.pre : return
        self.pre.add (e)
        e.post_add (self)

    def post_add (self, e) :
        if e in self.post : return
        self.post.add (e)
        e.pre_add (self)

    def cfl_add (self, e) :
        if e in self.cfl : return
        self.cfl.add (e)
        e.cfl_add (self)

    def __repr__ (self) :
        return "e%d:%s" % (self.nr, repr (self.label))

    def __str__ (self) :
        s = "e%d:%s" % (self.nr, repr (self.label))
        s += " pre " + str (list (self.pre))
        s += " post " + str (list (self.post))
        s += " cfl " + str (list (self.cfl))
        #s += " m " + str (self.m)
        #s += ";"
        return s

class PES :
    def __init__ (self) :
        self.events = []
        self.m = 0
        self.minimal = set ()

        # memoized causality and conflict relations
        self.__cau_rel = set () # E x E \cup E  -- see is_cau
        self.__cfl_rel = {} # E x E -> Bool     -- see is_cfl

    def add_event (self, label=None, pre=set(), cfl=set()) :
        e = Event (len (self.events), label)
        for ep in pre : e.pre_add (ep)
        for ep in cfl : e.cfl_add (ep)
        self.events.append (e)
        return e

    def update_minimal (self) :
        self.minimal = set ()
        for e in self.events :
            if len (e.pre) == 0 :
                self.minimal.add (e)

    def update_minimal_hint (self, e) :
        if len (e.pre) == 0 :
            self.minimal.add (e)
        elif e in self.minimal :
            self.minimal.remove (e)

    def new_mark (self) :
        self.m += 1
        return self.m

    def iter_max_events (self) :
        for e in self.events :
            if len (e.post) == 0 : yield e

    def get_empty_config (self) :
        return Configuration (self)

    def get_config_from_mark (self, m) :
        config = Configuration (self)
        while True :
            found = False
            for e in config.enabled () :
                if e.m == m :
                    config.add (e)
                    found = True
                    break
            if not found :
                return config

    def get_config_from_set (self, events) :
        # XXX - this function will silently return some configuration
        # contained in "events" when they are not causally closed or
        # contain conflicts
        if not isinstance (events, set) :
            events = set (events)
        config = Configuration (self)
        while True :
            s = config.enabled () & events
            if len (s) == 0 : return config
            config.add (s.pop ())

    def iter_causal_past (self, events) :
        m = self.new_mark ()
        work = events
        while len (work) :
            e = work.pop ()
            e.m_cc = m
            yield e
            for ep in e.pre :
                if ep.m_cc != m : work.append (ep)

    def iter_causal_future (self, events) :
        m = self.new_mark ()
        work = events
        while len (work) :
            e = work.pop ()
            e.m_cc = m
            yield e
            for ep in e.post :
                if ep.m_cc != m : work.append (ep)

    def mark_causal_past (self, m, events) :
        for e in self.iter_causal_past (events) : e.m = m
    def mark_causal_future (self, m, events) :
        for e in iter_causal_future (events) : e.m = m
    def get_local_config (self, events) :
        m = self.new_mark ()
        self.mark_causal_past (m, events)
        return self.get_config_from_mark (m) 

    def set_cfls (self, e, indep) :

        if len (e.post) :
            raise Exception, "Trying to compute conflicts for non maximal event %s" % repr (e)

        # mark in red local configuration
        # mark in blue all immediate conflicts of those in local config
        mred = self.new_mark ()
        mblue = self.new_mark ()
        mgreen = self.new_mark ()
        work = [e]
        l = []
        ll = []
        while len (work) :
            ep = work.pop ()
            ep.m = mred
            l.append (ep)
            for epp in ep.pre :
                if epp.m != mred : work.append (epp)
            for epp in ep.cfl :
                epp.m = mblue
                ll.append (epp)
        #print 'red', l
        #print 'blue', ll
        #print 'mred', mred, 'mblue', mblue, 'mgreen', mgreen

        # for remaining events, process them once their local config is
        # processed, color them in green
        work = list (self.minimal)
        while len (work) :
            ep = work.pop ()
            #print 'at', ep
            assert (ep.m != mgreen)
            if ep.m == mblue : continue
            if ep.m != mred :
                #print '  are indep %s %s %s' % (repr (e), repr (ep), indep.get (e.label, ep.label))
                if not indep.get (e.label, ep.label) :
                    e.cfl_add (ep)
                    continue
            ep.m = mgreen
            for e2 in ep.post :
                # if every event in e2's preset is green or red, e2 is ready
                found = False
                for e3 in e2.pre :
                    if e3.m != mgreen :
                        found = True
                        break
                if not found :
                    #print '  adding', e2
                    work.append (e2)

    def write (self, f, fmt='dot') :
        if isinstance (f, basestring) : f = open (f, 'w')
        if fmt == 'dot' : return self.__write_dot (f)
        raise Exception, "'%s': unknown output format" % fmt

    def __write_dot (self, f) :
        f.write ('digraph {\n')
        f.write ('\t/* events */\n')
        f.write ('\tnode\t[shape=box style=filled fillcolor=gray80];\n')
        for e in self.events :
            f.write ('\t%s [label="%s"];\n' % (id (e), repr (e)))

        f.write ('\n\t/* causality and conflict */\n')
        nrpre, nrcfl = 0, 0
        for e in self.events :
            for ep in e.pre :
                f.write ('\t%s -> %s;\n' % (id (ep), id (e)))
                nrpre += 1
            for ep in e.cfl :
                if id (e) < id (ep) : continue
                f.write ('\t%s -> %s [style=dashed arrowhead=none color=red];\n' % (id (ep), id (e)))
                nrcfl += 1
        f.write ('\n\tgraph [label="%d events\\n%d causalities\\n%d conflicts"];\n}\n' % \
                (len (self.events), nrpre, nrcfl))


    def __sorted_pair (self, e1, e2) :
        if id (e1) <= id (e2) : return e1, e2
        else : return e2, e1

    def in_caus (self, e1, e2) :
        if e1 == e2 : return False

        # if we have already processed [e2] in the past
        if e2 in self.__cau_rel :
            return (e1, e2) in self.__cau_rel
        else :
            self.__cau_rel.add (e2) # marks that we have processed [e2]
            v = False
            for e in self.iter_causal_past ([e2]) :
                self.__cau_rel.add ((e, e2))
                if e == e1 : v = True
            return v

    def in_cfl (self, e1, e2) :
        v = self.__in_cfl (e1, e2)
        print "cfl %s %s %s" % (repr (e1), repr (e2), v)
        return v
    def __in_cfl (self, e1, e2) :
        k = self.__sorted_pair (e1, e2)
        try :
            return self.__cfl_rel[k]
        except KeyError :
            if e1 == e2 : return False
            m = self.new_mark ()
            self.mark_causal_past (m, [e1])
            for e in self.iter_causal_past ([e2]) :
                for ep in e.cfl :
                    if ep.m == m :
                        self.__cfl_rel[k] = True
                        return True
            self.__cfl_rel[k] = False
            return False

    def iter_max_confs (self) :
        c = Configuration (self)
        l = []
        enum_max_conf (self, c, [], -1, l)
        return l

    def __repr__ (self) :
        return repr (self.events)

    def __str__ (self) :
        return "events %s minimal %s" % (repr (self.events), repr (self.minimal))
    
# vi:ts=4:sw=4:et:
