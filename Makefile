# $Header$

# List of pseudo targets
.PHONY: all clean dist

# Output directory
OUTPUTDIR=$(HOME)/pythonroot

# Install directory for globally callable scripts
SCRIPTDIR=$(HOME)/pythonscripts

# collect all source files in SRC
SRC := $(patsubst ./%,%,$(shell find . -print))

# list of all files that just have to be copied
SRC_PY      := $(sort $(filter _xist/%.py,$(SRC)))
SRC_SCRIPTS := $(sort $(filter scripts/%.py,$(SRC)))
SRC_CP      := $(SRC_PY)

DEP_CP      := $(patsubst _xist/%,$(OUTPUTDIR)/xist/%,$(SRC_CP))
DEP_SCRIPTS := $(patsubst scripts/%,$(SCRIPTDIR)/%,$(SRC_SCRIPTS))
DEP_PYC     := $(patsubst _xist/%.py,$(OUTPUTDIR)/xist/%.pyc,$(SRC_PY))

SRC := $(SRC_CP) $(SRC_SCRIPTS)

DEP := $(DEP_CP) $(DEP_SCRIPTS)

all: $(OUTPUTDIR)/xist $(OUTPUTDIR)/xist/ns $(SCRIPTDIR) $(DEP) $(OUTPUTDIR)/xist/helpers.so

install:
	python setup.py install

dist:
	doc2txt.py --title History --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials NEWS.xml NEWS
	doc2txt.py --title "Requirements and installation" --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials INSTALL.xml INSTALL
	doc2txt.py --title "Documentation" --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials HOWTO.xml HOWTO
	python setup.py sdist --formats=bztar,gztar
	python setup.py bdist --formats=rpm
	#rm NEWS INSTALL HOWTO

windist:
	python D:\\\\Programme\\\\Python21\\\\Scripts\\\\doc2txt.py --title History --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials NEWS.xml NEWS
	python D:\\\\Programme\\\\Python21\\\\Scripts\\\\doc2txt.py --title "Requirements and installation" --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials INSTALL.xml INSTALL
	python D:\\\\Programme\\\\Python21\\\\Scripts\\\\doc2txt.py --title "Documentation" --import xist.ns.specials --import xist.ns.abbr --import xist.ns.doc --import xist.ns.specials HOWTO.xml HOWTO
	python setup.py sdist --formats=zip
	python setup.py bdist --formats=wininst
	rm NEWS INSTALL HOWTO

$(OUTPUTDIR)/xist:
	mkdir -p $(OUTPUTDIR)/xist

$(OUTPUTDIR)/xist/ns:
	mkdir -p $(OUTPUTDIR)/xist/ns

$(SCRIPTDIR):
	mkdir -p $(SCRIPTDIR)

clean:
	rm $(DEP) $(DEP_PYC) $(OUTPUTDIR)/xist/helpers.so _xist/helpers.o

$(DEP_CP): $(OUTPUTDIR)/xist/% : _xist/%
	cp $< $(patsubst _xist/%, $(OUTPUTDIR)/xist/%, $<)

$(DEP_SCRIPTS): $(SCRIPTDIR)/% : scripts/%
	cp $< $(patsubst scripts/%, $(SCRIPTDIR)/%, $<)

$(OUTPUTDIR)/xist/helpers.so: _xist/helpers.c
	gcc -c -I/usr/local/include/python2.1 -g -O6 -fpic _xist/helpers.c -o _xist/helpers.o
	gcc -shared _xist/helpers.o -o $(OUTPUTDIR)/xist/helpers.so

