all: epydoc

epydoc:
	#epydoc -o apidoc --html -v --graph all --no-private --exclude="__pkginfo__" --exclude="setup" -n "Logilab's common library" ../
	mkdir apidoc
	epydoc -o apidoc --html -v --no-private --exclude="__pkginfo__" --exclude="setup" -n "Logilab's common library" ../

clean:
	rm -rf apidoc
