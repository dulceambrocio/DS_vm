# data-science-vm
Vagrant, Ansible and python data science libraries for data-science needs

This a Vagrant+Ansible data science setup.

Pre-requirements are:

<p>
<strong>brew</strong> (to install Ansible) https://brew.sh 
</p>
<p>
<strong>Vagrant 1.9.1+</strong> https://www.vagrantup.com/downloads.html
</p>
<p>
<strong>Ansible 2.2.1.0+</strong> https://valdhaus.co/writings/ansible-mac-osx/
</p>
<p>
<strong>VirtualBox</strong> https://www.virtualbox.org/wiki/Downloads
</p>
The vBox uses ubuntu/trusty64 with an automatic config.vm.network = en0 (update it as needed)

TO RUN: 
vagrant up --provision

AFTER RUN:
vagrant ssh

Once you are inside the vm:
sudo services postgresql restart (needed to connect from outside the vm to the db)
