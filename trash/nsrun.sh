#!/bin/bash
#Run the simulation application inside a namespace
APP=$1
MAX=$2

for i in {0..9}
    do
    sudo ip netns exec drone$i bash -c "xterm -hold -e ./main.py drone$i $APP 1 $MAX random_walk gossipfo ipv4 -r node &"
done

