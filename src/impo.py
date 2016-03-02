#!/usr/bin/env python

if __name__ == '__main__' :

    import impo
    import sys
    m = impo.Main ()
    m.main ()
    sys.exit (0)

    try :
        import sys
        import impo
        m = impo.Main ()
        m.main ()
        #pod.test.test19 ()
    except KeyboardInterrupt :
        print 'impo: interrupted'
        sys.exit (1)
    except Exception as e :
        print 'impo: error: %s' % str (e)
        sys.exit (1)
    sys.exit (0)

# vi:ts=4:sw=4:et:
