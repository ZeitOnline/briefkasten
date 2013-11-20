pyversion = 2.7
python = python$(pyversion)
buildoutcfg = development
cfgs = buildout development deployment

all: buildout

$(cfgs): %: %.cfg bin/buildout
	bin/buildout -c $@.cfg

buildout.cfg:
	ln -s $(buildoutcfg).cfg buildout.cfg

bin/buildout: bin/pip
	bin/pip install zc.buildout

bin/python bin/pip:
	virtualenv .

clean:
	git clean -fXd

.PHONY: all $(cfgs) clean
