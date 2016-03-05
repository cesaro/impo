
APP13fig3a
----------

Fig. 3a in
https://lipn.univ-paris13.fr/~andre/documents/precise-robustness-analysis-of-time-petri-nets-with-inhibitor-arcs.pdf

This is a rather meaningless benchmark, where IMPO does not terminate. So you
need to bound the number of events::

  --par t1,t1m,t1p
  --par t2,t2m,t2p
  --max-ev 15

APP13fig3b
----------
Fig. 3b in 
https://lipn.univ-paris13.fr/~andre/documents/precise-robustness-analysis-of-time-petri-nets-with-inhibitor-arcs.pdf

Intuition:

Under the reference valuation (in the net),
transition t1 is so slow that t2 always fires before, unless prevented by t3,
which disables t2. Only in that case t1 can fire, and necessarily after t3.

There is a typo in the paper, and place B is not marked. But it should.

Parameters::

  --par t1,t1m,t1p
  --par t2,t2m,t2p
  --par t3,t3m,t3p

Reference valuation will be read from the net.

JLR15
-----

Fig. 8 in 
http://www.irccyn.ec-nantes.fr/~lime/publis/jovanovic-TSE-14.pdf

The Alternating Bit Protocol. We need to bound here as well.

tr t2 [a,a+1] p2    -> p2 p5
tr t5 [b,b+1] p4    -> p4 p7
tr t7 [0,c] p5      ->
tr t9 [0,d] p7      ->
tr t13 [e,2] p9     -> p6 p10
tr t16 [0,f] p11    -> p8 p12

a + 1 = ap
b + 1 = bp

fig2
----

fig5
----

