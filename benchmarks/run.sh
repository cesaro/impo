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
  --par t3,t3m,t3p \
  --seq

./src/impo.py benchmarks/own/fischer3.pnml \
  --par p1_setid0,,b \
  --par p1_setid1,,b \
  --par p1_setid2,,b \
  --par p2_setid0,,b \
  --par p2_setid1,,b \
  --par p2_setid2,,b \
  --par p1_pause,x, \
  --par p2_pause,x, \
  --seq-sem --no-unl
fi

if false; then
	true
fi

./src/impo.py benchmarks/own/latch.pnml \
  --par env_2,tlo,tlo \
  --par env_3,thold,thold \
  --par env_4,thi,thi \
  --par not1_up,not1_up,not1_up \
  --par not1_down,not1_down,not1_down \
  --par not2_up,not2_up,not2_up \
  --par not2_down,not2_down,not2_down \
  --par xor_down0,xor_down,xor_down \
  --par xor_down1,xor_down,xor_down \
  --par xor_up01,xor_up,xor_up \
  --par xor_up10,xor_up,xor_up \
  --par and_up,and_up,and_up \
  --par and_downxor,and_down,and_down \
  --par and_downck,and_down,and_down \
  --par latch_up,latch_up,latch_up \
  --seq-sem \
  #--no-unl
