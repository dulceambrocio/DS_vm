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
<<p>
The vBox uses ubuntu/trusty64 with an automatic config.vm.network = en0 (update it as needed with en1, en2)
</p>
<p>
<strong>TO RUN:</strong> 
vagrant up --provision
</p>

<p>
<strong>AFTER RUN:</strong>
Once the installation is finished you need to connect to the vm
vagrant ssh
</p>

<<p>
<strong>Once you are inside the vm:</strong>
sudo service postgresql restart (needed to connect from outside the vm to the db)
</p>
