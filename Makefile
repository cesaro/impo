
include defs.mk

.PHONY: all tags

all:
	-./src/impo.py --help

tags : $(SRCS)
	ctags -R src/

-include $(DEPS)

