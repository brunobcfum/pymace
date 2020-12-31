#!/bin/bash
mkdir reports &> /dev/null
mkdir /opt/genesis_sim &> /dev/null
cp -R * /opt/genesis_sim
pip3 install -r requirements.txt
sudo apt install xterm

echo "Change visudo to add path of omnet and preserve env"