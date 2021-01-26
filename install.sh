#!/bin/bash
mkdir reports &> /dev/null
sudo mkdir /opt/pymace &> /dev/null
sudo cp -R * /opt/pymace
sudo pip3 install -r requirements.txt
sudo apt install xterm batctl

echo "Manually install OMNet++ and CORE"
echo "Change visudo to add path of omnet and preserve env"