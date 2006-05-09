#MKHTML=mkdoc
#MKHTMLOPTS=--doctype book --param toc.section.depth=2  --target html --stylesheet single-file
#SRC=.

#TXTFILES:= $(wildcard *.txt)
#TARGET := $(TXTFILES:.txt=.html)

all: apydoc

#%.html: %.txt
#        ${MKHTML} ${MKHTMLOPTS} $<

apydoc:
	epydoc --html -n "Logilab's common library" ../modutils.py ../textutils.py ../fileutils.py

clean:
	rm -f *.html
