"""
Usage:

impo [OPTIONS] PNMLFILE

where PNMLFILE is the path to a file storing a Time Petri Net in Tina's PNML
format.
The delay intervals associated to each transition in PNMLFILE will become the
reference valuation (unless redefined with the options --v0-*, see below).  The
OPTIONS placeholder corresponds to zero or more of the following options:

 --help, -h
   Shows this message.

 --par-transition=T,X,Y
   Parametrizes transition T, setting parameter X as the earliest firing delay,
   and Y as the latest firing delay. The option can naturally appear multiples
   times.

 --v0-par=X,N
   Sets the reference valuation for parameter X to N.

 --v0-transition=T,N1,N2
   Sets the reference valuation for the earliest/latest firing delay parameters
   of transition T to, respectively, N1 and N2.

 --par-transition=T
   (Not yet implemented)

 --par-all-transitions
   (Not yet implemented)

 --k0
   (Not yet implemented)

 --no-asserts
   Disables defensive programming verifications.

 --output=OUTPUTPATH
   Save the output of the command to OUTPUTPATH
   (Not yet implemented)
"""

try :
    from util import *

    import os
    import sys
    import resource
    import networkx
    import argparse
    import random
    import tempfile
    import intervals

    import ptnet
    import pes

    from test import *

except ImportError, e:
    error_missing_package (e)

if sys.version_info < (2, 7, 0) or sys.version_info >= (3, 0, 0) :
    print ("")
    print ("*** ERROR ***")
    print ("This tool relies on Python 2.7!!")
    print ("Install Python 2.7 or modify the first line of the file 'po-discovery.py' so that it calls Python 2.7")
    print ("")
    sys.exit (1)

class MyArgumentParser (argparse.ArgumentParser) :
    def format_help (self) :
        return __doc__
    def parse_args (self) :
        if len (sys.argv) == 1 :
            self.print_usage ()
            self.exit (1)
        return argparse.ArgumentParser.parse_args (self)

class Main :
    def __init__ (self) :

        self.arg_pnmlfile = None        # string
        self.arg_param_efd = None       # map from transition names to param names
        self.arg_param_lfd = None       # map from transition names to param names
        self.arg_v0 = None              # map from parameter names to floats

        self.net = None                 # the net object
        self.bp = None                  # the unfolding of the net 
        self.pes = None                 # the PES associated to the unfolding
        self.configs = None             # list of lists of maximal events

        self.paramtab = None            # a ParamTable object, containing all parameters
        self.v0 = None                  # map from Params to float
        self.efd = None                 # map from Transitions to either a Param or float
        self.lfd = None                 # map from Transitions to either a Param or float

        self.k0const = None             # initial constraint on parameters (string)
        self.v0const = None             # p1 = v0[p1], p2 = v0[p2], etc (string)

        self.final_const = None         # final constraint

    def parse_cmdline_args (self) :

        self.arg_param_efd = {}
        self.arg_param_lfd = {}
        self.arg_v0 = {}

        self.arg_pnmlfile = './benchmarks/fig2.pnml'
        self.arg_param_lfd['b'] = 'x1'
        self.arg_param_lfd['c'] = 'x2'
        self.arg_v0['x1'] = 1
        self.arg_v0['x2'] = 3.5

        #self.arg_pnmlfile = './benchmarks/tina/abp.pnml'
        #self.arg_param_efd['t2'] = 'x1'
        #self.arg_param_lfd['t2'] = 'x2'
        #self.arg_param_efd['t3'] = 'x3'
        #self.arg_v0['x1'] = 12

        return

        cmd_choices = [
                "compare-independence",
                "extract-dependence",
                "extract-log",
                "net-stats",
                "dump-log",
                "dump-pes",
                "dump-bp",
                "dump-encoding",
                "dump-merge",
                "discover",
                ]
        eq_choices = [
                "id",
                "sp-1place",
                "sp-pre-singleton",
                "sp-pre-max",
                "sp-smt",
                "sp-smt-post",
                "ip-smt",
                "ev-only",
                ]
        usage = "pod [OPTION]... CMD {LOG,PNML} [DEPFILE]\n" + \
                "Try 'pod --help' for more information."
        p = MyArgumentParser (prog="pod", usage = usage)
        #g = p.add_mutually_exclusive_group ()
        p.add_argument ("--log-truncate", type=int)
        p.add_argument ("--log-fraction-truncate", type=float)
        p.add_argument ("--log-unique", action="store_true")
        p.add_argument ("--log-only")
        p.add_argument ("--log-negative")
        p.add_argument ("--log-exclude")
        p.add_argument ("--no-asserts", action="store_true")
        p.add_argument ("--output")
        p.add_argument ("--eq", choices=eq_choices, default="id")
        p.add_argument ("--smt-timeout", type=int, default=60)
        p.add_argument ("--smt-nr-places", type=int)
        p.add_argument ("--smt-min-places", type=int)
        p.add_argument ("--smt-max-places", type=int)
        p.add_argument ("--smt-pre-distinct", action="store_true")
        #p.add_argument ("--smt-merge-post", action="store_true")
        p.add_argument ("--smt-forbid-self", action="store_true")
        #p.add_argument ("--format", choices=["pdf","dot","pnml"])

        p.add_argument ('cmd', metavar="COMMAND", choices=cmd_choices)
        p.add_argument ('log_pnml', metavar="LOGFILE/PNML")
        p.add_argument ('depen', metavar="DEPENFILE", nargs="?", default=None)

        args = p.parse_args ()
        #print "pod: args:", args

        self.arg_command = args.cmd
        self.arg_depen_path = args.depen
        self.arg_eq = args.eq
        self.arg_log_path = args.log_pnml
        self.arg_log_trunc = args.log_truncate
        self.arg_log_trunc_frac = args.log_fraction_truncate
        self.arg_log_unique = args.log_unique
        self.arg_log_negative = args.log_negative
        self.arg_smt_timeout = args.smt_timeout
        self.arg_smt_pre_distinct = args.smt_pre_distinct
        #self.arg_smt_merge_post = args.smt_merge_post
        self.arg_smt_forbid_self = args.smt_forbid_self
        self.arg_no_asserts = args.no_asserts

        # nr-places translates to min-places and max-places
        if args.smt_nr_places != None :
            self.arg_smt_min_places = args.smt_nr_places
            self.arg_smt_max_places = args.smt_nr_places
        else :
            self.arg_smt_min_places = args.smt_min_places
            self.arg_smt_max_places = args.smt_max_places

        # at most one of log-trunc and log-trunc-frac
        if self.arg_log_trunc_frac != None and self.arg_log_trunc != None :
                raise Exception, "At most one of --log-truncate and --log-fraction-truncate"

        if self.arg_command not in \
            ["extract-dependence", "dump-log", "net-stats", "extract-log"] :
            if self.arg_depen_path == None :
                raise Exception, "Missing argument: expected path to a dependence file"

        if args.log_only != None :
            try :
                self.arg_log_only = [int (x) for x in args.log_only.split (",")]
            except Exception :
                raise Exception, "'%s': expected a comma-separated list of numbers" % (args.log_only)
        if args.log_exclude != None :
            try :
                self.arg_log_exclude = [int (x) for x in args.log_exclude.split (",")]
            except Exception :
                raise Exception, "'%s': expected a comma-separated list of numbers" % (args.log_exclude)

        if args.output != None :
            self.arg_output_path = args.output
        else :
            d = {
                "extract-dependence" : "dependence.txt",
                "extract-log"        : "log.xes",
                "dump-pes"           : "pes.dot",
                "dump-bp"            : "bp.pdf",
                "dump-encoding"      : "encoding.smt2",
                "discover"           : "output.pnml"}
            self.arg_output_path = d.get (self.arg_command, "output.txt")
        for opt in [
                    "arg_command",
                    "arg_depen_path",
                    "arg_no_asserts",
                    "arg_log_path",
                    "arg_log_trunc",
                    "arg_log_trunc_frac",
                    "arg_log_only",
                    "arg_log_exclude",
                    "arg_log_negative",
                    "arg_log_unique",
                    "arg_smt_timeout",
                    "arg_smt_pre_distinct",
                    #"arg_smt_merge_post",
                    "arg_smt_forbid_self",
                    "arg_smt_min_places",
                    "arg_smt_max_places",
                    "arg_eq",
                    "arg_output_path",
                    ] :
            output_pair (sys.stdout, opt, self.__dict__[opt], 20, "pod: ")

    def main (self) :

        # parse command line
        self.parse_cmdline_args ()

        # load the net
        self.net = load_tpn (self.arg_pnmlfile, "pnml", "impo")
        print 'impo: note: delay interval closure info (open, close) will be completely ignored!'

        # setup v0, lower and upper bounds (efd, lfd), and k0
        self.setup_params_v0_k0 ()

        # unfold with cunf
        self.export_and_unfold ()

        # transform into PES
        print 'impo: unf > pes: extracting underlying PES from unfolding'
        self.pes = pes.bp_to_pes (self.bp)
        print 'impo: unf > pes: done'

        # relabel the PES so event labels point to self.net
        self.relabel_pes ()

        # extract maximal configurations
        #self.pes.write (sys.stdout, 'dot')
        print 'impo: pes > conf: enumerating all maximal PES configurations'
        mxconfs = self.pes.iter_max_confs ()
        avg = avg_iter (len (c.events) for c in mxconfs)
        print 'impo: pes > conf: done, %d confs, %.2f ev/conf (avg)' % (len (mxconfs), avg)

        # IMPO method :
        # for every maximal config:
        # - generate string constraint with clocks and params
        # - hide clock variables
        # - discard if v0-compatible
        # - negate and add to the final conjunction
        # add k0 to the final conjunction

        l = []
        for c in mxconfs :
            print 'impo: con > eq: ===== new configuration:'
            print 'impo: con > eq:   all', long_list (c.events)
            print 'impo: con > eq:   mx ', long_list (c.maximal ())
            print 'impo: con > eq:   cex', long_list (c.cex ())
            self.assert_is_max_conf (c)

            const = ConfigConst (c, self.efd, self.lfd, self.v0const)
            const.generate ()

            #print 'impo: con > eq: existential quantification of clock/doe/dod vars'
            print 'impo: con > eq: existential quantification'
            const2 = const.hide ()

            print 'impo: con > eq: checking whether v0 compatible'
            if const2.does_include_v0 () :
                print 'impo: con > eq: v0-compatible, skipping'
                continue

            print 'impo: con > eq: negating constraint'
            const3 = const2.negate ()
            l.append (const3)

        # compute final conjunction, adding k0
        self.compute_final_constraint (l)

        # print results
        self.print_results ()

    def print_results (self) :
        print '=' * 80
        print 'Constraint k0:'
        l = self.k0const.splitlines ()
        l = l[1:-1]
        print '\n'.join (l)
        print

        print 'Reference valuation v0:'
        l = self.v0const.splitlines ()
        l = l[1:-1]
        print '\n'.join (l)
        print

        print 'Generated constraint:'
        print self.final_const
        print

    def compute_final_constraint (self, l) :
        query = 'simplify and (\n (* k0 constraint *)\n'
        query += self.k0const + ',\n\n'
        for cst in l : query += '(%s),\n\n' % cst.const
        query += ')\n'

        # simplify with polyop
        print 'impo: simplifying conjunction of negated constraints'
        output = polyop (query, 'impo:  ')
        print 'impo:   query:', long_str (repr (query))
        print 'impo:   result:', long_str (repr (output))
        output = polyop_replace_ors (output)
        print 'impo:   replace:', long_str (repr (output))
        if output == 'error' :
            raise Exception, "Internal error: polyop returned `error' result file"
        self.final_const = output

    def setup_params_v0_k0 (self) :
        # formatting
        pl1 = pl = 0
        if len (self.arg_param_efd) >= 1 :
            pl1 = max (len (s) for s in self.arg_param_efd.values ())
        if len (self.arg_param_lfd) >= 1 :
            pl  = max (len (s) for s in self.arg_param_lfd.values ())
        if pl1 > pl : pl = pl1
        tl = 0
        if len (self.net.trans) :
            tl = max (len (t.name) for t in self.net.trans)

        # set up lower and upper bounds, parametric or non-parametric
        netvalue = {}
        self.efd = {}
        self.lfd = {}
        self.paramtab = ParamTable ()
        print 'impo: setting up parametrized delays:'
        for t in self.net.trans :
            if t.name in self.arg_param_efd :
                p = self.paramtab.get (self.arg_param_efd[t.name])
                del self.arg_param_efd[t.name]
                self.efd[t] = p
                netvalue[p] = t.delay.lower
                print "impo:   %-*s  (transition %.*s, lower)" % (pl, p.name, tl, t.name)
            else :
                self.efd[t] = t.delay.lower
            if t.name in self.arg_param_lfd :
                p = self.paramtab.get (self.arg_param_lfd[t.name])
                del self.arg_param_lfd[t.name]
                self.lfd[t] = p
                netvalue[p] = t.delay.upper
                print "impo:   %-*s  (transition %.*s, upper)" % (pl, p.name, tl, t.name)
            else :
                self.lfd[t] = t.delay.upper

        # define the reference valuation, either coming from command line or
        # from the net
        self.v0 = {}
        print 'impo: setting up reference valuation v0:'
        for p in self.paramtab :
            if p.name in self.arg_v0 :
                self.v0[p] = self.arg_v0[p.name]
                del self.arg_v0[p.name]
                print "impo:   %.*s  %-10f (from cmdline)" % (pl, p.name, self.v0[p])
            else :
                self.v0[p] = netvalue[p]
                print "impo:   %.*s  %-10f (from tpn)" % (pl, p.name, self.v0[p])

        # we removed used pairs from the argument mappings, if we still have
        # somthing, warning
        for name in self.arg_param_efd :
            print "impo: WARNING: transition '%s' not found, but you gave a parameter for its efd" % name
        for name in self.arg_param_lfd :
            print "impo: WARNING: transition '%s' not found, but you gave a parameter for its lfd" % name
        for name in self.arg_v0 :
            print "impo: WARNING: parameter '%s' not defined, but you gave its reference value" % name

        # set up an initial constraint, stating than delay intervals are really
        # so
        print 'impo: setting up initial constraint k0'
        self.k0const = 'and (\n'
        for t in self.net.trans :
            if isinstance (self.efd[t], Param) or isinstance (self.lfd[t], Param) :
                self.k0const += ' %s <= %s, (* transition %s *)\n' % \
                        (str (self.efd[t]), str (self.lfd[t]), t.name)
        self.k0const += ')\n'

        # build v0const
        self.v0const = 'and (\n'
        for p,v in self.v0.items () :
            self.v0const += ' %s = %s,\n' % (str (p), v)
        self.v0const += ')\n'

        # check that v0const implies k0const
        print 'impo: checking that v0 implies k0'
        for t in self.net.trans :
            if isinstance (self.efd[t], Param) :
                low = self.v0[self.efd[t]]
            else :
                low = self.efd[t]
            if isinstance (self.lfd[t], Param) :
                high = self.v0[self.lfd[t]]
            else :
                high = self.lfd[t]
            if low > high :
                s = "error: v0 does not imply k0: "
                s += "transition '%s': `%s <= %s' does not hold" % \
                        (t.name, self.efd[t], self.lfd[t])
                raise Exception, s

    def relabel_pes (self) :
        for e in self.pes.events :
            t = self.net.trans_lookup_name (e.label.name)
            if t == None :
                raise Exception, \
                        'Internal error: cannot map event "%s" in PES to transition' % repr (e)
            e.label = t

    def assert_is_max_conf (self, c) :
        assert len (c.enabled ()) == 0

    def assert_is_max_conf_mx (self, mx) :
        print 'impo: pes > conf: asserting is maximal configuration'
        # verify that every two maximal events of a config are not in conflict
        for e in mx :
            for ee in mx :
                assert not self.pes.in_cfl (e, ee)
        # so causal closure is indeed a configuration, maximal?
        c = self.pes.get_local_config (mx)
        assert len (c.enabled ()) == 0
        print 'impo: pes > conf: done, it is max conf'

    def export_and_unfold (self) :
        netpath = None
        cufpath = None
        try :
            # export in ll_net into temporary file
            print 'impo: net > unf: exporting net in ll_net format'
            fnet, netpath = tempfile.mkstemp (suffix='.ll_net')
            fcuf, cufpath = tempfile.mkstemp (suffix='.cuf')
            os.close (fcuf)
            f = os.fdopen (fnet, 'w')
            self.net.write (f, 'pep')
            f.close ()
            print 'impo: net > unf: done'

            # call cunf
            print 'impo: net > unf: running cunf ...'
            cmd = ['cunf', netpath]
            cmd.append ('--save=%s' % cufpath)
            cmd.append ('--stats')
            cmd.append ('--cutoff=none')
            cmd.append ('--max-events=5')
            print 'impo: net > unf: cmd', cmd
            exitcode, out = runit (cmd, prefix='impo: net > unf: ')
            if exitcode != 0 :
                raise Exception, 'cunf unfolder: exit code %d, output: "%s"' % (exitcode, out)
            print 'impo: net > unf: done, exit code 0'
            #print 'impo: net > unf: cunf stdout:', repr (out)

            # load unfolding
            self.bp = load_bp (cufpath, 'impo: net > cuf')

        finally :
            # remove temporary files
            if netpath != None : os.unlink (netpath)
            if cufpath != None : os.unlink (cufpath)

class Param :
    def __init__ (self, name) :
        self.name = name
    def __str__ (self) :
        return str (self.name)

class ParamTable :
    def __init__ (self) :
        self.__tab = {}
    def get (self, name) :
        try :
            return self.__tab[name]
        except KeyError :
            p = Param (name)
            self.__tab[name] = p
            return p
    def __getitem__ (self, name) :
        return self.get (name)
    def __iter__ (self) :
        return iter (self.__tab.values ())
    def __str__ (self) :
        return str (self.__tab)

class Var (str) :
    pass

class ConfigConst :
    def __init__ (self, c, efd, lfd, v0const) :
        self.c = c          # the configuration
        self.const = ""      # the constraint
        self.__tab = {}     # map from objects to Vars (only for vars that are not params)
        self.hidevars = []  # range of the __tab map (seen as a function)
        self.efd = efd
        self.lfd = lfd
        self.v0const = v0const

    def getvar (self, obj) :
        try :
            return self.__tab[obj]
        except KeyError :
            if isinstance (obj, pes.Event) :
                name = 'e%d' % obj.nr
            else :
                name = str (obj)
            v = Var (name)
            self.__tab[obj] = v
            self.hidevars.append (v)
            return v

    def does_include_v0 (self) :
        # polyop gives correct result only if we have no variables to hide (ask Etienne)
        if len (self.hidevars) :
            raise Exception, 'Internal error: v0 inclusion checking bug'
        query = 'included %s in %s' % (self.v0const, self.const)

        output = polyop (query, 'impo: con > eq:  ')
        print 'impo: con > eq:   query:', repr (query)
        print 'impo: con > eq:   result:', repr (output)
        return output == 'yes'

    def hide (self) :
        # nothing to do if we already hid the clock variables
        if len (self.hidevars) == 0 : return self

        # hide variables with polyop
        query = 'hide ('
        query += ', '.join (str (v) for v in self.hidevars)
        query += ') in ' + self.const

        output = polyop (query, 'impo: con > eq:  ')
        print 'impo: con > eq:   query:', long_str (repr (query))
        print 'impo: con > eq:   result:', long_str (repr (output))
        output = polyop_replace_ors (output)
        print 'impo: con > eq:   replace:', long_str (repr (output))

        if output == 'error' :
            raise Exception, "Internal error: polyop returned `error' result file"

        # build a new constraint and return it
        c = ConfigConst (self.c, self.efd, self.lfd, self.v0const)
        c.const = polyop_replace_ors (output)
        return c

    def negate (self) :
        query = 'simplify not (%s)' % self.const
        output = polyop (query, 'impo: con > eq:  ')
        print 'impo: con > eq:   query:', long_str (repr (query))
        print 'impo: con > eq:   result:', long_str (repr (output))
        output = polyop_replace_ors (output)
        print 'impo: con > eq:   replace:', long_str (repr (output))

        if output == 'error' :
            raise Exception, "Internal error: polyop returned `error' result file"

        # build a new constraint and return it
        c = ConfigConst (self.c, self.efd, self.lfd, self.v0const)
        c.const = output
        return c

    def __str__ (self) :
        return self.const

    def generate (self) :
        self.const = 'and (\n'
        self.__gen_delays_met ()
        self.__gen_cex_not_overtaken ()
        self.const += ')\n'

    def __gen_delays_met (self) :
        # delays of all events in the configuration are met (first condition)
        for e in self.c :
            ve = self.getvar (e)
            vdoe = self.__gen_doe (e)

            # efd(e.label) <= e - doe_e
            self.const += ' (* delays met for %s *)\n' % repr (e)
            self.const += " %s <= %s - %s,\n" % \
                    (str (self.efd[e.label]), str (ve), str (vdoe))

            # e - doe_e <= lfd(e.label)
            s = "%s - %s <= %s," % \
                    (str(ve), str (vdoe), str (self.lfd[e.label]))
            if self.lfd[e.label] == float ('inf') : s = '(* %s *)' % s
            self.const += ' ' + s + '\n\n'

    def __gen_cex_not_overtaken (self) :
        # latest firing delays of conflicting extensions of the configuration
        # are not overtaken; we profit from the fact that the configuration is
        # maximal, to compute the conflicting extensions (and skip adding the
        # third constraint ;)
        assert len (self.c.enabled ()) == 0
        for e in self.c.cex () :
            vdod = self.__gen_dod (e)
            vdoe = self.__gen_doe (e)

            # dod_e <= doe_e + lfd(e.label)
            self.const += ' (* delay not overtaken for cex %s *)\n' % repr (e)
            s = "%s <= %s + %s," % \
                    (str (vdod), str (vdoe), str (self.lfd[e.label]))
            if self.lfd[e.label] == float ('inf') : s = '(* %s *)' % s
            self.const += ' ' + s + '\n\n'

    def __gen_doe (self, e) :
        self.const += " (* doe(%s) = max %s *)\n" % (repr (e), list (e.pre))
        v = self.getvar ('doe_e%d' % e.nr)
        self.__gen_max_const_eq ([self.getvar (ep) for ep in e.pre], v)
        self.const += "\n"
        return v

    def __gen_dod (self, e) :

        # we need to find those events in the self.c that are in immediate
        # conflict with e (the reasons why e is a conflicting extension ;)
        # we relay here on the fact that e.cfl contains ONLY the immediate
        # conflicts, due to the the fact that we constructed the PES by direct
        # transformation of a branching process ;)
        l = [ep for ep in e.cfl if ep in self.c.events]

        self.const += " (* dod(%s) = min %s *)\n" % (repr (e), l)
        v = self.getvar ('dod_e%d' % e.nr)
        self.__gen_min_const_eq ([self.getvar (ep) for ep in l], v)
        self.const += "\n"
        return v


    def __gen_max_const_eq (self, l, m) :
        # max (all vars in l) == m
        self.__gen_max_const_le (l, m)
        self.__gen_max_const_ge (l, m)

    def __gen_max_const_le (self, l, m) :
        # max (all vars in l) <= m
        for e in l :
            self.const += " %s <= %s,\n" % (str (e), str (m))

    def __gen_max_const_ge (self, l, m) :
        # max (all vars in l) >= m
        if len (l) == 0 : return
        self.const += " ("
        for e in l[:-1] :
            self.const += "%s >= %s or " % (str (e), str (m))
        self.const += "%s >= %s),\n" % (str (l[-1]), str (m))

    def __gen_min_const_eq (self, l, m) :
        # min (all vars in l) == m
        self.__gen_min_const_le (l, m)
        self.__gen_min_const_ge (l, m)

    def __gen_min_const_le (self, l, m) :
        # min (all vars in l) <= m
        if len (l) == 0 : return
        self.const += " ("
        for e in l[:-1] :
            self.const += "%s >= %s or " % (str (m), str (e))
        self.const += "%s >= %s),\n" % (str (m), str (l[-1]))

    def __gen_min_const_ge (self, l, m) :
        # min (all vars in l) >= m
        for e in l :
            self.const += " %s <= %s,\n" % (str (m), str (e))

# vi:ts=4:sw=4:et:
