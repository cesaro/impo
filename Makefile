
include defs.mk

.PHONY: all tags

all:
	-./src/impo.py --help
	#-./src/impo.py benchmarks/own/fig2.pnml 
	benchmarks/run.sh

tags : $(SRCS)
	ctags -R src/

-include $(DEPS)

