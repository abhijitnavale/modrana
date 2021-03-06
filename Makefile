PKGNAME=modrana
VERSION=$(shell awk '/Version:/ { print $$2 }' packaging/$(PKGNAME).spec)
RELEASE=$(shell awk '/Release:/ { print $$2 }' packaging/$(PKGNAME).spec | sed -e 's|%.*$$||g')
TAG=modrana-$(VERSION)

PYTHON2=python2
PYTHON3=python3
PYTHON=$(PYTHON2)

RSYNC=rsync

SOURCEDIR=modrana_source
BUILDDIR=modrana_build
EXCLUDEFILE=packaging/fedora/exclude.txt
EXCLUDESAILFISH=packaging/sailfish/exclude.txt
# lists a few additional items to exclude for Harbour packages
EXCLUDEHARBOUR=packaging/sailfish/exclude_harbour.txt

DESTDIR=/

default: all

all:
	rm -rf $(SOURCEDIR)
	rm -rf $(BUILDDIR)
	mkdir $(SOURCEDIR)
	mkdir $(BUILDDIR)
	cp -r core $(SOURCEDIR)
	cp -r data $(SOURCEDIR)
	cp -r modules $(SOURCEDIR)
	cp -r run $(SOURCEDIR)
	cp -r themes $(SOURCEDIR)
	cp -r modrana.py $(SOURCEDIR)
	cp -r version.txt $(SOURCEDIR)

rsync:
	# cleanup the source tree
	$(RSYNC) -ar --exclude-from $(EXCLUDEFILE) $(SOURCEDIR)/ $(BUILDDIR)

rsync-sailfish: sailfish-qml-mangle
	# cleanup the source tree for a Sailfish OS package
	$(RSYNC) -ar --exclude-from $(EXCLUDESAILFISH) $(SOURCEDIR)/ $(BUILDDIR)

rsync-harbour: sailfish-qml-mangle
	# first mark modrana.py as not executable as Harbour RPM validator does not like that
	# for some reason (not like you could not just run it with python3 modrana.py...)
	chmod -x $(SOURCEDIR)/modrana.py
	# also mark the startup scripts as not executable to make the Harbour RPM validator happy
	chmod -x $(SOURCEDIR)/run/*

	# cleanup the source for a Sailfish OS Harbour package
	$(RSYNC) -ar --exclude-from $(EXCLUDESAILFISH) --exclude-from $(EXCLUDEHARBOUR) $(SOURCEDIR)/ $(BUILDDIR)

clean:
	-rm *.tar.gz
	rm -rf $(SOURCEDIR)
	rm -rf $(BUILDDIR)

sailfish-qml-mangle:
	bash packaging/sailfish/sailfish_qml_mangle.sh $(SOURCEDIR)

bytecode-python2:
	-python2 -m compileall $(BUILDDIR)

bytecode-python3:
	-python3 -m compileall $(BUILDDIR)

install:
	-mkdir -p $(DESTDIR)/usr/share/modrana
	cp -r $(BUILDDIR)/* $(DESTDIR)/usr/share/modrana
	# install *all* available icons - just in case :)
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/48x48/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/64x64/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/128x128/apps
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/256x256/apps
	cp packaging/icons/modrana/48x48/modrana.png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/
	cp packaging/icons/modrana/64x64/modrana.png $(DESTDIR)/usr/share/icons/hicolor/64x64/apps/
	cp packaging/icons/modrana/128x128/modrana.png $(DESTDIR)/usr/share/icons/hicolor/128x128/apps/
	cp packaging/icons/modrana/256x256/modrana.png $(DESTDIR)/usr/share/icons/hicolor/256x256/apps/
	cp packaging/fedora/modrana-qml.png $(DESTDIR)/usr/share/icons/hicolor/64x64/apps/
	# install the desktop file
	-mkdir -p $(DESTDIR)/usr/share/applications/
	cp packaging/fedora/modrana.desktop $(DESTDIR)/usr/share/applications/
	cp packaging/fedora/modrana-qt5.desktop $(DESTDIR)/usr/share/applications/
	# install the startup scripts
	-mkdir -p $(DESTDIR)/usr/bin
	cp packaging/fedora/modrana $(DESTDIR)/usr/bin/
	cp packaging/fedora/modrana-gtk $(DESTDIR)/usr/bin/
	cp packaging/fedora/modrana-qt5 $(DESTDIR)/usr/bin/

install-sailfish:
	-mkdir -p $(DESTDIR)/usr/share/harbour-modrana
	cp -r $(BUILDDIR)/* $(DESTDIR)/usr/share/harbour-modrana
	# install the icon
	-mkdir -p $(DESTDIR)/usr/share/icons/hicolor/86x86/apps/
	cp packaging/icons/modrana/86x86/modrana.png $(DESTDIR)/usr/share/icons/hicolor/86x86/apps/harbour-modrana.png
	# install the desktop file
	-mkdir -p $(DESTDIR)/usr/share/applications/
	cp packaging/sailfish/harbour-modrana.desktop $(DESTDIR)/usr/share/applications/
	
tag:
	git tag -a -m "Tag as $(TAG)" -f $(TAG)
	@echo "Tagged as $(TAG)"

archive: tag local

local:
	@rm -f ChangeLog
	@make ChangeLog
	@make VersionFile
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ $(TAG) > $(PKGNAME)-$(VERSION).tar
	mkdir -p $(PKGNAME)-$(VERSION)
	cp ChangeLog $(PKGNAME)-$(VERSION)/
	cp version.txt $(PKGNAME)-$(VERSION)/
	tar -rf $(PKGNAME)-$(VERSION).tar $(PKGNAME)-$(VERSION)
	gzip -9 $(PKGNAME)-$(VERSION).tar
	rm -rf $(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

rpmlog:
	@git log --pretty="format:- %s (%ae)" $(TAG).. |sed -e 's/@.*)/)/'
	@echo

ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

VersionFile:
	echo $(VERSION) > version.txt

bumpver:
	@NEWSUBVER=$$((`echo $(VERSION) |cut -d . -f 3` + 1)) ; \
	NEWVERSION=`echo $(VERSION).$$NEWSUBVER |cut -d . -f 1,2,4` ; \
	DATELINE="* `LANG=c date "+%a %b %d %Y"` `git config user.name` <`git config user.email`> - $$NEWVERSION-1"  ; \
	cl=`grep -n %changelog packaging/modrana.spec |cut -d : -f 1` ; \
	tail --lines=+$$(($$cl + 1)) packaging/modrana.spec > speclog ; \
	(head -n $$cl packaging/modrana.spec ; echo "$$DATELINE" ; make --quiet rpmlog 2>/dev/null ; echo ""; cat speclog) > packaging/modrana.spec.new ; \
	mv packaging/modrana.spec.new packaging/modrana.spec ; rm -f speclog ; \
	sed -i "s/Version: $(VERSION)/Version: $$NEWVERSION/" packaging/modrana.spec ; \

.PHONY: clean install tag archive local

test:
	nosetests -w tests -v
