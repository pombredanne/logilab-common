all: epydoc

epydoc:
	#epydoc -o apidoc --html -v --graph all --no-private --exclude="__pkginfo__" --exclude="setup" -n "Logilab's common library" ../
	mkdir apidoc
	epydoc -o apidoc --html -v --no-private --exclude="__pkginfo__" --exclude="setup" -n "Logilab's common library" $(shell dirname $(CURDIR))/build/lib/logilab/common

clean:
	rm -rf apidoc
