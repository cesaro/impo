
include defs.mk

.PHONY: all tags

all:
	#-./src/impo.py --help
	-./src/impo.py benchmarks/fig2.pnml 

tags : $(SRCS)
	ctags -R src/

-include $(DEPS)

