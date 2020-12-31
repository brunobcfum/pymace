#!/bin/bash

echo "This script is part of the genesis project."
echo "This script creates several Linux namespaces and TAP interfaces in them"
echo ""

OPT=$1
NDS=$2
PROGRAM=$(basename $0)

usage() {
    echo "usage: sudo ${PROGRAM} [option] [number of nodes]" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "   add                           Adds everything automatically" >&2
    echo "   bat                           Adds nodes for using with BATMAN" >&2
    echo "   rasp                          Adds nodes for using with a Raspberry PI emulator" >&2
    echo "   vm                            Adds nodes for using with a virtual machine" >&2
    echo "   riot                          Adds nodes for using with RIOT OS" >&2
    echo "   del                           Removes everything automatically" >&2
    echo "   -h, --help:                   Prints this help" >&2
}

TAPNAME="tap"
VMTAPNAME="vmtap"
NODENAME="drone"
BRNAME="br"

if [ "$OPT" == "-h" ]; then
    usage
    exit 1
fi

if [ "$OPT" == "--help" ]; then
    usage
    exit 1
fi

if [ -z "${SUDO_USER}" ]; then
    echo 'Environment variable $SUDO_USER required; Please run with `sudo`'
    exit 1
fi

if [ -z "${OPT}" ]; then
    echo 'Please specify one option'
    usage
    exit 1
fi

if [ -z "${NDS}" ]; then
    echo 'Please specify number of nodes'
    usage
    exit 1
fi



if [ "$OPT" == "add" ]; then
    echo "[INFO] Creating TAP interfaces"
    for i in {0..9}
        do
        sudo ip tuntap add mode tap $TAPNAME$i
    done
    echo "[INFO] Creating namespaces"
    for i in {0..9}
        do
        sudo ip netns add $NODENAME$i
    done
    echo "[INFO] Adding interfaces to namespaces"
    for i in {0..9}
        do
        sudo ip link set $TAPNAME$i netns $NODENAME$i
    done
    echo "[INFO] Configuring interfaces"
    for i in {0..9}
        do
        hex=`printf '%02x\n' $(($i+1))`
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.0.$(($i+1))/255.255.255.0 broadcast 10.0.0.255 dev $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i address 0A:AA:00:00:00:$hex"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i up"
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 127.0.0.1/255.255.255.0 dev lo"
        sudo ip netns exec $NODENAME$i bash -c "ip link set lo up"
    done
fi

if [ "$OPT" == "del" ]; then
    echo "[INFO] Removing namespaces and interfaces"
    for i in $(seq 0 $NDS)
        do
        sudo ip netns delete $NODENAME$i
        sudo ip link del $TAPNAME$i
        sudo ip link del $VMTAPNAME$i
        sudo ip link del $BRNAME$i
    done
fi

if [ "$OPT" == "vm" ]; then
    echo "[INFO] Creating TAP interfaces"
    for i in $(seq 0 $NDS)
        do
        sudo ip tuntap add mode tap $TAPNAME$i
        sudo ip tuntap add mode tap $VMTAPNAME$i
    done

    echo "[INFO] Configuring interfaces"
    for i in $(seq 0 $NDS)
        do
        hex=`printf '%02x\n' $(($i+1))`
        ip=`printf '%03d\n' $(($i+101))`
        sudo ip addr add 10.0.0.$ip/255.255.255.0 broadcast 10.0.0.255 dev $TAPNAME$i
        sudo ip link set $TAPNAME$i up
    done
fi

if [ "$OPT" == "bat" ]; then
    echo "[INFO] Creating TAP interfaces"
    for i in $(seq 0 $NDS)
        do
        sudo ip tuntap add mode tap $TAPNAME$i
    done
    echo "[INFO] Creating namespaces"
    for i in $(seq 0 $NDS)
        do
        sudo ip netns add $NODENAME$i
    done
    echo "[INFO] Adding interfaces to namespaces"
    for i in $(seq 0 $NDS)
        do
        sudo ip link set $TAPNAME$i netns $NODENAME$i
    done
    echo "[INFO] Configuring interfaces"
    for i in $(seq 0 $NDS)
        do
        hex=`printf '%02x\n' $(($i+1))`
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.0.$(($i+1))/255.255.255.0 broadcast 10.0.0.255 dev $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i address 0A:AA:00:00:00:$hex"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i up"
        sudo ip netns exec $NODENAME$i bash -c "batctl if add $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set up bat0"
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.1.$(($i+1))/255.255.255.0 broadcast 10.0.1.255 dev bat0"
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 127.0.0.1/255.255.255.0 dev lo"
        sudo ip netns exec $NODENAME$i bash -c "ip link set lo up"
    done
fi

if [ "$OPT" == "rasp" ]; then
    echo "[INFO] Creating TAP interfaces"
    for i in {0..9}
        do
        sudo ip tuntap add mode tap $TAPNAME$i
    done
    echo "[INFO] Creating namespaces"
    for i in {0..9}
        do
        sudo ip netns add $NODENAME$i
    done
    echo "[INFO] Adding interfaces to namespaces"
    for i in {0..9}
        do
        sudo ip link set $TAPNAME$i netns $NODENAME$i
    done
    echo "[INFO] Configuring interfaces"
    for i in {0..9}
        do
        hex=`printf '%02x\n' $(($i+1))`
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.0.$(($i+1))/255.255.255.0 broadcast 10.0.0.255 dev $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i address 0A:AA:00:00:00:$hex"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i up"
        sudo ip netns exec $NODENAME$i bash -c "ip link add br0 type bridge"
        sudo ip netns exec $NODENAME$i bash -c "ip tuntap add mode tap vmtap0"
        sudo ip netns exec $NODENAME$i bash -c "ip link set vmtap0 up"
        sudo ip netns exec $NODENAME$i bash -c "ip link set br0 up"
        sudo ip netns exec $NODENAME$i bash -c "batctl if add $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set up bat0"
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.1.$(($i+1))/255.255.255.0 broadcast 10.0.1.255 dev bat0"
        sudo ip netns exec $NODENAME$i bash -c "brctl addif br0 bat0"
        sudo ip netns exec $NODENAME$i bash -c "brctl addif br0 vmtap0"
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 127.0.0.1/255.255.255.0 dev lo"
        sudo ip netns exec $NODENAME$i bash -c "ip link set lo up"
    done
fi

if [ "$OPT" == "riot" ]; then

    echo "[INFO] Creating TUN/TAP interfaces"
    for i in {0..9}
        do
        sudo ip tuntap add mode tap $TAPNAME$i
        sudo ip tuntap add mode tap $TAPNAME\d$i
    done
    echo "[INFO] Creating namespaces"
    for i in {0..9}
        do
        sudo ip netns add $NODENAME$i
    done
    echo "[INFO] Adding interfaces to namespaces"
    for i in {0..9}
        do
        sudo ip link set $TAPNAME$i netns $NODENAME$i
        sudo ip link set $TAPNAME\d$i netns $NODENAME$i
    done
    echo "[INFO] Creating Bridge interfaces"
    for i in {0..9}
        do
        sudo ip netns exec $NODENAME$i bash -c "ip link add name br0 type bridge"
    done
    echo "[INFO] Configuring interfaces"
    for i in {0..9}
        do
        sudo ip netns exec $NODENAME$i bash -c "ip addr add 10.0.0.$(($i+1))/255.255.255.0 broadcast 10.0.0.255 dev $TAPNAME$i"
        sudo ip netns exec $NODENAME$i bash -c "ip link set dev $TAPNAME$i master br0 || exit 1"
        sudo ip netns exec $NODENAME$i bash -c "ip link set dev $TAPNAME\d$i master br0 || exit 1"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME$i up"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $TAPNAME\d$i up"
        sudo ip netns exec $NODENAME$i bash -c "ip link set $BRNAME$i up"
    done
fi
