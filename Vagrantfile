Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/trusty64"
  config.vm.box_url = "http://files.vagrantup.com/trusty64.box"  

  config.vm.network "forwarded_port", guest: 8000, host: 7669
  config.vm.network "forwarded_port", guest: 5432, host: 7670

  config.vm.network "public_network", bridge: "en0: Wi-Fi (AirPort)"

  #config.vm.synced_folder "./project", "/home/vagrant/project"

  config.vm.provider "virtualbox" do |vb|
	vb.memory = 2048
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provision/vagrant.yml"
  end

end
