This repo is deprecated. Newer commits will be made in:
https://github.com/brunobcfum/moaemu

# pymace - Python Mobile Ad-Hoc Computing Emulator
This software is part of the paper: MACE: Mobile Ad-Hoc Computing Emulator

## Installation

### Network emulators

*CORE*

CORE can be downloaded here: https://github.com/coreemu/core/releases
This was tested with release 7.2.1 and instructions on how to install can be found here: https://coreemu.github.io/core/install.html

Core can be installed using virtual environments, but this work was created considering CORE was installed locally using:
./install.sh -l

*OMNet++*

OMNet++ Installation guide can be found here:
https://omnetpp.org/doc/omnetpp/InstallGuide.pdf

This work has been tested with OMNet++ 5.6.2

*Since OMNet does not work well with high traffic load in emulated mode, it is being deprecated as an option.* 

### Linux

Some packages need to be installed on Linux:

- batctl: Used for configuring the B.A.T.M.A.N routing protocol.
- xterm: Used when opening terminals inside the namespaces. Only reason is because it is more compact to open several simultaneously.


### Python

The following Python packages are required:

flask
flask_socketio==4.3.2
apscheduler
ping3
geopy
pymobility

This work has been testes with Python 3.8

### PyMACE

It is recommended to place pymace on /opt. It can be done by running the script install.sh