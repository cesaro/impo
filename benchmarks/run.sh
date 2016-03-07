#!/bin/sh

set -x

if false; then
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

fi

./src/impo.py benchmarks/own/fischer2.pnml \
  --par p1_if_id=0,a,a \
  --par p2_if_id=0,a,a \
  --par p1_setid0,c,c \
  --par p1_setid1,c,c \
  --par p1_setid2,c,c \
  --par p2_setid0,c,c \
  --par p2_setid1,c,c \
  --par p2_setid2,c,c \
  --par p1_pause,x,x \
  --par p2_pause,x,x \
  --seq

#  --par p1_if_id=0,a,b \
#  --par p2_if_id=0,a,b \
#  --par p1_setid0,c,d \
#  --par p1_setid1,c,d \
#  --par p1_setid2,c,d \
#  --par p2_setid0,c,d \
#  --par p2_setid1,c,d \
#  --par p2_setid2,c,d \
#  --par p1_pause,x,x \
#  --par p2_pause,x,x \


# Constraint k0:
#  a <= b, (* transition p1_if_id=0 *)
#  a <= b, (* transition p2_if_id=0 *)
#  c <= d, (* transition p1_setid0 *)
#  c <= d, (* transition p1_setid1 *)
#  c <= d, (* transition p1_setid2 *)
#  c <= d, (* transition p2_setid0 *)
#  c <= d, (* transition p2_setid1 *)
#  c <= d, (* transition p2_setid2 *)
#  x <= x, (* transition p1_pause *)
#  x <= x, (* transition p2_pause *)
#  0 <= x,
#  0 <= a,
#  0 <= c,
# 
# Reference valuation v0:
#  x = 10.0,
#  b = 1.0,
#  d = 1.0,
#  a = 0.0,
#  c = 0.0,
# 
# Generated constraint:
#   c >= 0
# & a >= 0
# & x > d
# & d >= a
# & b >= a
# & d >= c
# 
# or
# 
#   c >= 0
# & b >= a
# & x >= 0
# & a > d
# & d >= c

