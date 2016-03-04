#!/bin/sh

set -x

./src/impo.py benchmarks/own/fig5.pnml \
	--p t3,n1l,n1h \
	--p t4,n1l,n1h \
	--p t5,n2l,n2h \
	--p t6,n2l,n2h \
	--p t7,al,ah \
	--p t8,al,ah \
	--p t9,al,ah \
	--no-unli
