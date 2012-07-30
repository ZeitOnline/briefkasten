
pyversion = 2.7
python = python$(pyversion)
buildoutcfg = development
cfgs = buildout development deployment

all: buildout

$(cfgs): %: %.cfg bin/buildout
	bin/buildout -c $@.cfg

buildout.cfg:
	ln -s $(buildoutcfg).cfg buildout.cfg

bin/buildout: buildout.cfg bootstrap.py
	$(python) bootstrap.py -d

clean:
	rm -rf .installed.cfg bin/buildout buildout.cfg

.PHONY: all $(cfgs) clean
