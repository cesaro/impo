#!/bin/sh

set -x

./src/impo.py benchmarks/own/fig5.pnml \
  --par t3,n1l,n1h \
  --par t4,n1l,n1h \
  --par t5,n2l,n2h \
  --par t6,n2l,n2h \
  --par t7,al,ah \
  --par t8,al,ah \
  --par t9,al,ah

./src/impo.py benchmarks/own/APP13fig3a.pnml \
  --par t1,t1m,t1p \
  --par t2,t2m,t2p \
  --max-ev 10

./src/impo.py benchmarks/own/APP13fig3b.pnml \
  --par t1,t1m,t1p \
  --par t2,t2m,t2p \
  --par t3,t3m,t3p
