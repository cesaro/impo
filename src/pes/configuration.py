
class Configuration :
    #def __init__ (self, pes, events=set()) :
    def __init__ (self, pes) :
        self.pes = pes
        self.events = set ()
        self.__en = set (pes.minimal)
        self.__max = set ()

    def copy (self, other) :
        self.pes = other.pes
        self.events = other.events
        self.__en = other.__en
        self.__max = other.__max

    def deep_copy (self, other) :
        self.pes = other.pes
        self.events = set (other.events)
        self.__en = set (other.__en)
        self.__max = set (other.__max)

    def clone (self) :
        config = Configuration (self.pes)
        config.deep_copy (self)
        return config

    def intersect_with (self, other) :
        if self.pes != other.pes :
            raise ValueError, "Intersection between configurations of different PESs"
        result = Configuration (self.pes)
        intersection = self.events & other.events
        while True :
            s = result.__en & intersection
            if len (s) == 0 : break
            result.add (s.pop ())
        self.copy (result)
        return self

    def enabled (self) :
        return self.__en

    def maximal (self) :
        return self.__max

    def extensions (self) :
        # returns ex(C)
        pass

    def iter_cex (self) :
        # trivial algorithm
        for e in self.events :
            for ep in e.post :
                if ep.pre <= self.events and ep not in self.__en :
                    yield ep

    def add (self, e) :
        if e not in self.__en :
            raise ValueError, "Event %s is not enabled cand cannot be added" % repr (e)

        # add it
        self.events.add (e)

        # update maximal events
        self.__max -= e.pre
        self.__max.add (e)

        # update enabled events; first all those enabled in conflict with
        # e must go away, as well as e
        self.__en.remove (e)
        self.__en -= e.cfl

        # second, we add events enabled by the new addition, all of which
        # are in e's postset (if their history is in the configuration and
        # no conflict is in there)
        for ep in e.post :
            if self.__is_enabled (ep) :
                self.__en.add (ep)

    def __is_enabled (self, e) :
        # computes if an event is enabled, the hard way, e's history shall
        # be in the configuration and no conflict of it can be
        return e.pre <= self.events and e.cfl.isdisjoint (self.events)

    def update_enabled_hint (self, e) :
        # updates __en with this event if it is not in __en (eg, because it
        # has been added after creating this configuration)
        if self.__is_enabled (e) :
            self.__en.add (e)
        elif e in self.__en :
            self.__en.remove (e)

    def find_h0 (self, t, indep) :
        # find the largest history in this configuration for t under indep
        # discarding the hippies (checking if e.post is in what remains)
        # returns set of concurrent (maximal) events

        # keep two lists, move dependent events to dep; mark hippies with m
        m = self.pes.new_mark ()
        dep = []
        work = list (self.__max)
        #print 'mark m', m
        while len (work) :
            e = work.pop ()
            #print 'eval t "%s" e "%s"' % (t, e)
            assert (e.m != m)
            if not indep.get (e.label, t) :
                dep.append (e)
                continue
            e.m = m
            for ep in e.pre :
                # ep is ready iff ep.post \cap this config is all marked
                found = False
                for epp in ep.post & self.events:
                    if epp.m != m :
                        found = True
                        break
                if not found :
                    work.append (ep)
        #print 'return', dep
        return dep

    def is_ex (self, e) :
        # return whether e is an extension of the configuration
        pass

    def is_en (self, e) :
        return e in self.__en

    def __iter__ (self) :
        return iter (self.events)

    def __repr__ (self) :
        return repr (list (self.events))

    def __str__ (self) :
        return "conf %s max %s en %s" % (list(self.events), list(self.__max), list(self.__en))

# vi:ts=4:sw=4:et:
