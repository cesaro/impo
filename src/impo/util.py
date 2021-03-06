
def error_missing_package (exception) :
    print 'ERROR!'
    print 'It seems that your python installation is missing some package.'
    print 'This tool requires, among others, the following packages:'
    print '* resource, networkx, argparse, random, z3, ptnet, pes'
    print 'The runtime reported the following error:\n\n', str (exception), '\n'
    print 'You might want to use "easy_install --user PACKAGE"'
    print ''
    import sys
    sys.exit (1)

try :
    import os
    import subprocess
    import tempfile
    import ptnet
except ImportError, e:
    error_missing_package (e)

def output_dict (f, d, prefix='impo: ') :
    n = max ([len (k) for k in d])
    l = list (d)
    l.sort ()
    for k in l :
        output_pair (f, k, d[k], n, prefix)

def output_pair (f, k, v, n, prefix='', fmt='%s') :
    f.write (prefix + ('%-*s : ' + fmt + '\n') % (n, k, v))

def size_human (n) :
    n = float (n)
    if n < 3073 :
        return n, 'B', '%dB' % int (n)
    n /= 1024
    if n < 1024 :
        return n, 'K', '%.1fK' % n
    n /= 1024
    if n < 1024 :
        return n, 'M', '%.2fM' % n
    n /= 1024
    if n < 1024 :
        return n, 'G', '%.2fG' % n
    n /= 1024
    return n, 'T', '%.2fG' % n

def load_tpn (path, fmt="pnml", prefix='impo') :
    net = ptnet.tpn.Net ()
    try :
        size = os.path.getsize (path)
        _, _, hum = size_human (size)
        print "%s: loading net (TPN) file '%s' (%s)" % (prefix, path, hum)
        f = open (path, 'r')
        net.read (f, fmt=fmt)
        f.close ()
    except Exception as e :
        raise Exception, "'%s': %s" % (path, e)
    print "%s: done, %d transitions, %d places" % (prefix, len (net.trans), len (net.places))
    print "%s: first 5 transitions are:" % prefix
    for t in net.trans[:5] :
        print "%s:  %s" % (prefix, str (t))
    return net

def load_bp (path, prefix='impo') :
    bp = ptnet.unfolding.Unfolding ()
    try :
        size = os.path.getsize (path)
        _, _, hum = size_human (size)
        print "%s: loading cuf file '%s' (%s)" % (prefix, path, hum)
        f = open (path, 'r')
        bp.read (f)
        f.close ()
    except Exception as e :
        raise Exception, "'%s': %s" % (path, e)
    print "%s: done, %d events, %d conditions" % (prefix, len (bp.events), len (bp.conds))
    print "%s: first 5 events are:" % prefix
    for e in bp.events[:5] :
        print "%s:  %s" % (prefix, str (e))
    return bp

def runit (args, timeout=-1, sh=False, prefix='impo: ') :
    print prefix, 'cmd:', args, 'timeout', timeout
    try :
        p = subprocess.Popen (args, bufsize=8192, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                preexec_fn=os.setsid, shell=sh)
    except Exception as e :
        raise Exception, \
                "Unable to run `%s' (accessible in the PATH?): %s" \
                % (args[0], str (e))

#    db ('pid', p.pid)
    try :
        killed = False
        s = ''
        p.stdin.close ()
        if timeout > 0 :
            tref = time.time ()
            while True :
                t = timeout - (time.time () - tref)
                if t <= 0 : t = 0
#                db ('select at', time.time () - tref, t)
                (r, w, x) = select.select ([p.stdout], [], [p.stdout], t)
#                db ('return at', time.time () - tref, r, w, x)
                if len (r) :
                    # read (n) waits for n bytes before returning
                    c = p.stdout.read (1)
                    if len (c) == 0 : break
                    s += c
                else :
#                    db ('killing', p.pid)
                    os.killpg (p.pid, signal.SIGTERM)
                    killed = True
                    break
        p.wait ()
        s += p.stdout.read ()
        return (p.returncode if not killed else 254, s)
    except KeyboardInterrupt :
        os.killpg (p.pid, signal.SIGKILL)
        p.wait ()
        raise

def polyop (query, prefix='impo: ', unlink=True) :
    inpath = None
    outpath = None
    try :
        # save the query into temp file
        fd, inpath = tempfile.mkstemp (suffix='.pop.ml')
        f = os.fdopen (fd, 'w')
        f.write (query)
        f.close ()

        # run polyop
        cmd = ['polyop', inpath]
        exitcode, out = runit (cmd, prefix=prefix)
        if exitcode != 0 :
            raise Exception, 'polyop: exit code %d, output: "%s"' % (exitcode, out)
        #print prefix, 'exit code 0'
        #print prefix, 'stdout: "%s"' % out

        # load result
        outpath = inpath + '.res'
        with open (outpath) as f : res = f.read ()

    finally :
        # remove temporary files, unless disabled by user
        if unlink :
            if inpath != None : os.unlink (inpath)
            if outpath != None : os.unlink (outpath)

    # strip and return
    return res.strip (' \t\n')

def polyop_replace_ors (const) :
    l = const.split ()
    #print 'tokenization', l
    for i in range (len (l)) :
        if l[i] == 'OR' : l[i] = 'or'
    return ' '.join (l)

def polyop_pretty_format (const) :
    l = const.split ()
    #print l
    if len (l) <= 2 : return const
    l[0] = '  ' + l[0]
    for i in range (len (l)) :
        if l[i] == '&' : l[i] = '\n&'
        if l[i] == 'or' : l[i] = '\n\nor\n\n '
    return ' '.join (l)

def avg_iter (it) :
    s = 0
    i = 0
    for x in it :
        s += x
        i += 1
    return float (s) / i

def long_list (ls, maxlen=10) :
    ls = list (ls)
    le = len (ls)
    if maxlen < 0 : maxlen = le
    s = "["
    s += ", ".join (repr (x) for x in ls[:maxlen])
    if le > maxlen :
        s += ", ... %d more]" % (le - maxlen)
    else :
        s += "]"
    return s

def long_str (s, maxlen=160) :
    if len (s) <= maxlen : return s
    _, _, hum = size_human (len (s) - maxlen)
    return s[:maxlen] + ' ... %s more' % hum

# vi:ts=4:sw=4:et:
