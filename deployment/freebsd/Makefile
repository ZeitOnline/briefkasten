PYTHON = python2.7
PYTHON_TARGETS = bin/python lib/python* include/python*
VIRTUALENV = virtualenv
develop = false

MFSBSD_URL = http://mfsbsd.vx.sk/files/iso/9/amd64/mfsbsd-se-9.2-RELEASE-amd64.iso
MFSBSD_FILENAME = $(lastword $(subst /, ,$(MFSBSD_URL)))
MFSBSD_PATH = downloads/$(MFSBSD_FILENAME)
MFSBSD_SHA = 4ef70dfd7b5255e36f2f7e1a5292c7a05019c8ce

VM_BASEFOLDER = $(abspath vm)
VM_NAME = briefkasten
VM_PATH = $(VM_BASEFOLDER)/$(VM_NAME)
VM_VBOX = $(VM_PATH)/$(VM_NAME).vbox
VM_BOOT_DISK = $(VM_PATH)/boot.vdi

# setting up the deployment

all: python bin/ploy

$(PYTHON_TARGETS): python

python:
	$(VIRTUALENV) --clear .

bin/buildout: bin/pip
	bin/pip install --upgrade --force-reinstall zc.buildout
	touch bin/buildout


ifeq ($(develop), false)
bin/ploy: python
	bin/pip install --upgrade --force-reinstall -r requirements.txt
else
bin/ploy: bin/buildout
	bin/pip install --upgrade --force-reinstall ansible
	touch bin/ansible
	bin/buildout
endif


# download required assets:

check-mfsbsd-download:
	echo "$(MFSBSD_SHA)  $(MFSBSD_PATH)" | shasum -c || rm -f $(MFSBSD_PATH)

downloads:
	mkdir -p downloads

$(MFSBSD_PATH): downloads
	wget -c "$(MFSBSD_URL)" -O $(MFSBSD_PATH)
	touch $(MFSBSD_PATH)

mfsbsd-download: check-mfsbsd-download $(MFSBSD_PATH)


# setup and manage a virtualbox instance:

$(VM_PATH):
	mkdir -p $(VM_PATH)

%.vdi: $(VM_PATH)
	VBoxManage createhd --filename $@ --size 102400 --format VDI


$(VM_VBOX): $(VM_BOOT_DISK)
	VBoxManage createvm --name $(VM_NAME) --basefolder $(VM_BASEFOLDER) --ostype FreeBSD_64 --register
	VBoxManage modifyvm $(VM_NAME) --memory 2048 --accelerate3d off --boot1 disk --boot2 dvd --acpi on --rtcuseutc on
	VBoxManage storagectl $(VM_NAME) --name "SATA" --add sata
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type dvddrive --port 0 --medium $(MFSBSD_PATH)
	VBoxManage storageattach $(VM_NAME) --storagectl "SATA" --type hdd --port 1 --medium $(VM_BOOT_DISK)

vm: mfsbsd-download $(VM_VBOX)

start-vm: vm
	-VBoxManage modifyvm $(VM_NAME) --natpf1 "ssh,tcp,,47022,,22" --natpf2 "https,tcp,,47023,,443"
	VBoxManage startvm $(VM_NAME)

stop-vm:
	VBoxManage controlvm $(VM_NAME) acpipowerbutton

destroy-vm:
	-VBoxManage controlvm $(VM_NAME) poweroff && sleep 2
	-VBoxManage unregistervm $(VM_NAME) --delete


# Configure an existing host:

bootstrap-host: bin/ploy
	./bin/ploy do vm-master bootstrap

configure-host: bin/ploy
	./bin/ploy playbook setup/vm-master.yml

setup-poudriere:  bin/ploy
	./bin/ploy playbook setup/poudriere.yml

build-packages:  bin/ploy
	./bin/ploy do vm-master build_packages

cert: etc/briefkasten.crt, etc/briefkasten.key

etc/briefkasten.crt, etc/briefkasten.key:
	openssl req -x509 -newkey rsa:2048 -keyout etc/briefkasten.key -out etc/briefkasten.crt -days 365 -nodes


# Create and configure the jails

start-jails:  bin/ploy
	bin/ploy start webserver
	bin/ploy start appserver
	bin/ploy start cleanser

configure-webserver:
	bin/ploy playbook setup/webserver.yml

configure-appserver:
	bin/ploy playbook setup/appserver.yml
	bin/ploy do appserver upload_project

configure-cleanser:
	bin/ploy playbook setup/cleanser.yml

configure-jails: configure-webserver configure-appserver configure-cleanser


# clean up:

clean: destroy-vm
	rm -rf bin lib include share

dist-clean: clean
	git clean -dxxf src

