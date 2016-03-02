
import sys
import net
import intervals
import xml.parsers.expat


class Transition (net.Transition) :
    def __init__ (self, name, delay) :
        net.Transition.__init__ (self, name)
        if delay.upper == float('inf') and delay.upper_inc == True :
            delay.upper_inc = False # normalization
        if delay.lower < 0.0 :
            raise Exception, 'Invalid interval: %s: lower bound lower than 0' % str (delay)
        if delay.lower == float ('inf') :
            raise Exception, 'Invalid interval: %s: lower bound is infinite' % str (delay)
        self.delay = delay

        print "Transition: new: name %s dly %s" % (name, delay)

    def __str__ (self) :
        s = net.Transition.__str__ (self)
        return s + " dly " + str (self.delay)

class Place (net.Place) :
    pass

class Net (net.Net) :
    def place_add (self, name, m0=0) :
        p = Place (name)
        self.places.append (p)
        if m0 : self.m0[p] = m0
        # print 'place_add', name, m0
        return p

    def trans_add (self, name, interval = intervals.FloatInterval ([0, float('inf')])) :
        t = Transition (name, interval)
        self.trans.append (t)
        # print 'trans_add', name
        return t

    def __write_pnml_interval_closure (self, ival) :
        if ival.lower_inc :
            return 'closed' if ival.upper_inc else 'closed-open'
        else :
            return 'open-closed' if ival.upper_inc else 'open'

    def __write_pnml (self, f, m=0) :
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s += '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">\n'
        s += '<net id="n1" type="http://www.laas.fr/tina/tpn">\n'
        s += '<name> <text>"%s" version "%s", by "%s"</text> </name>\n' % \
            (self.title, self.version, self.author)
        s += '<page id="page">\n'

        f.write (s + '\n<!-- places -->\n')
        tab = {}
        for p in self.places :
            if m != 0 and c.m != m : continue
            s = '<place id="p%d">\n' % len (tab)
            s += '<name><text>%s</text></name>\n' % repr (p)
            s += '<initialMarking><text>%d</text></initialMarking>\n' % self.m0[p]
            s += '</place>\n'
            f.write (s)
            tab[p] = len (tab)

        # [0, inf)
        a = intervals.FloatInterval ([0.0, float ('inf')])
        a.upper_inc = False

        f.write ('\n<!-- transitions -->\n')
        for t in self.trans :
            if m != 0 and t.m != m : continue
            s = '<transition id="t%d">\n' % len (tab)
            s += '<name><text>%s</text></name>\n' % repr (t)
            if t.delay != a :
                s += '<delay>\n'
                s += '<interval xmlns="http://www.w3.org/1998/Math/MathML" closure="%s">' \
                        % self.__write_pnml_interval_closure (t.delay)
                s += '<cn>%s</cn>' % t.delay.lower
                if t.delay.upper == float ('inf') :
                    s += '<ci>infty</ci>'
                else :
                    s += '<cn>%s</cn>' % t.delay.upper
                s += '</interval>\n</delay>\n' 
            s += '</transition>\n'
            f.write (s)
            tab[t] = len (tab)

        f.write ('\n<!-- flow relation -->\n')
        for p in self.places :
            if m != 0 and c.m != m : continue
            s = ''
            for t in p.pre :
                if m == 0 or t.m == m :
                    s += '<arc id="a%d" source="t%d" target="p%d" />\n' \
                            % (len (tab), tab[t], tab[p])
                    tab[t, p, 'a'] = len (tab)
            for t in p.post :
                if m == 0 or t.m == m :
                    s += '<arc id="a%d" source="p%d" target="t%d" />\n' \
                            % (len (tab), tab[p], tab[t])
                    tab[p, t, 'a'] = len (tab)
            for t in p.cont :
                if m == 0 or t.m == m :
                    s += '<!-- read arc: -->\n'
                    s += ' <arc id="ra%d" source="p%d" target="t%d" />\n' \
                            % (len (tab), tab[p], tab[t])
                    tab[p, t, 'ra'] = len (tab)
                    s += ' <arc id="ra%d" source="t%d" target="p%d" />\n' \
                            % (len (tab), tab[t], tab[p])
                    tab[t, p, 'ra'] = len (tab)
            f.write (s)

        f.write ('\n</page>\n</net>\n</pnml>\n')

    def __read_pnml_ival (self, d) :
        assert d['type'] == 'transition'

        # we have a 'closure' attribute if we found an <interval> entity
        # we have a 'lower' and or 'upper' attributes if we found an <cn> or
        # <ci> entities; it is an error to have one and not the others, or vice
        # versa
        if ('lower' in d and 'upper' not in d) or ('upper' in d and 'lower' not in d) :
            raise Exception, 'Found an <interval> entity with only one <cn> or <ci> entity'
        if 'closure' in d and 'lower' not in d :
            raise Exception, 'Found an <interval> entity with no nested <cn> or <ci> entities'
        if 'lower' in d and 'closure' not in d :
            raise Exception, 'Found an <cn> entity but no <interval> entity'

        if 'closure' not in d :
            # no <interval> element was found in the transition, assume [0,inf)
            a = intervals.FloatInterval ([0.0, float ('inf')])
            a.upper_inc = False
            return a

        lower = d['lower']
        upper = d['upper']
        upper = upper.strip (' \n\t')
        if upper == 'infty' : upper = 'inf'
        ival = intervals.FloatInterval ([lower, upper])

        cl = d['closure']
        if cl == 'closed' :
            pass
        elif cl == 'open' :
            ival.lower_inc = False
            ival.upper_inc = False
        elif cl == 'closed-open' :
            ival.upper_inc = False
        elif cl == 'open-closed' :
            ival.lower_inc = False
        else :
            raise Exception, 'Unexpected XML closure attribute in delay interval: "%s"' % cl
        return ival

    def __read_pnml (self, f) :
        # documentation:
        # http://www.pnml.org/papers/PNML-Tutorial.pdf
        par = xml.parsers.expat.ParserCreate ()
        par.StartElementHandler = self.__pnml_start
        par.EndElementHandler = self.__pnml_end
        par.CharacterDataHandler = self.__pnml_data

        self.__pnmlitm = {}
        self.__pnmlq = []
        self.__pnmldepth = 0
        self.__pnmlskipdepth = sys.maxint
        par.ParseFile (f)
        if len (self.__pnmlitm) == 0 :
            raise Exception, 'missplaced "%s" entity' % tag
        self.__pnmlq.append (self.__pnmlitm)

        idx = {}
        for d in self.__pnmlq :
            if 'id' not in d : d['id'] = 'xxx'
            if 'name' not in d : d['name'] = d['id']
            if d['type'] == 'place' :
                if 'm0' not in d : d['m0'] = 0
                idx[d['id']] = self.place_add (d['name'], int (d['m0']))
                idx[d['id']].pid = d['id']
            elif d['type'] == 'transition' :
                ival = self.__read_pnml_ival (d)
                idx[d['id']] = self.trans_add (d['name'], ival)
                idx[d['id']].tid = d['id']
            elif d['type'] == 'net' :
                self.title = d['name']
        for d in self.__pnmlq :
            if d['type'] != 'arc' : continue
            if d['source'] not in idx or d['target'] not in idx :
                raise Exception, 'Arc with id "%s" has unknown source or target' % d['id']
            weight = 1
            if 'weight' in d :
                weight = int (d['weight'])
                #print "arc id '%s' with weight %d" % (d["id"], weight)
            idx[d['source']].post_add (idx[d['target']], weight)

        del self.__pnmlitm
        del self.__pnmlq

    def __pnml_start (self, tag, attr):
        self.__pnmldepth += 1
        #print "START", repr (tag), attr, "depth", self.__pnmldepth, "skip depth", self.__pnmlskipdepth
        if self.__pnmldepth >= self.__pnmlskipdepth : return

        if tag == 'net' :
            if len (self.__pnmlitm) != 0 :
                raise Exception, 'Missplaced XML tag "net"'
            self.__pnmlitm = {}
            self.__pnmlitm['type'] = 'net'

        elif tag in ['place', 'transition', 'arc'] :
            if len (self.__pnmlitm) == 0 :
                raise Exception, 'Missplaced XML tag "%s"' % tag
            #print 'new! ', repr (self.__pnmlitm)
            for k in ['name', 'm0'] :
                if k in self.__pnmlitm :
                    self.__pnmlitm[k] = self.__pnmlitm[k].strip(' \n\t')
            self.__pnmlq.append (self.__pnmlitm)
            print '-- recoding', self.__pnmlitm
            self.__pnmlitm = {}
            self.__pnmlitm['type'] = tag
            self.__pnmlitm['id'] = attr['id']
            for k in ['source', 'target'] :
                if k in attr :
                    self.__pnmlitm[k] = attr[k]

        elif tag == 'name' :
            self.__pnmlitm['data'] = 'name'
            self.__pnmlitm['name'] = ''
        elif tag == 'initialMarking' :
            self.__pnmlitm['data'] = 'm0'
            self.__pnmlitm['m0'] = ''
        elif tag == 'inscription' :
            self.__pnmlitm['data'] = 'weight'
            self.__pnmlitm['weight'] = ''
        elif tag == 'interval' :
            self.__pnmlitm['closure'] = attr['closure'] if 'closure' in attr else 'closed'
        elif tag == 'cn' or tag == 'ci' :
            # first time we hit cn or ci, it is the lower bound
            # second time, the upper bound
            if 'lower' not in self.__pnmlitm :
                self.__pnmlitm['data'] = 'lower'
                self.__pnmlitm['lower'] = ''
            else :
                self.__pnmlitm['data'] = 'upper'
                self.__pnmlitm['upper'] = ''

        # bug if inscription is an arc weight !!!!
        elif tag in ['toolspecific', 'graphics', 'arctype'] :
            self.__pnmlskipdepth = self.__pnmldepth
            return
        elif tag in ['page', 'pnml', 'text', 'delay'] :
            return
        # 'offset', 'position', 'dimension', 'fill', 'line', 'size', 'structure', 'unit', 'subunits', 'places'
        else :
            # this else clause is just to be on the safe side
            raise Exception, 'Unexpected XML tag "%s", probably I cannot handle this model. Is this a P/T model?' % tag

    def __pnml_end (self, tag):
        #print "END  ", repr (tag)
        self.__pnmldepth -= 1
        if self.__pnmldepth < self.__pnmlskipdepth :
            self.__pnmlskipdepth = sys.maxint
        if tag == 'text' and 'data' in self.__pnmlitm:
            del self.__pnmlitm['data']
            # this avoids recording data outside a <text> tag

    def __pnml_data (self, data):
        #data = data.strip(' \n\t') <- dangerous here, data can be split!!
        if len (data) == 0 : return

        #print "DATA ", repr (data)
        if 'data' not in self.__pnmlitm : return
        k = self.__pnmlitm['data']
        self.__pnmlitm[k] += data

