#!/bin/bash
TMAX=('10' '20' '50' '100' '500')
CURR_PWD=$(pwd)
DATA=`date +%d_%m_%Y_%H_%M`
#VERSION_DIR=`echo $1 | tr a-z A-Z`
VERSION_DIR='OUROBOROS'
REPORTS_DIR='reports/'
RESULTS_DIR="reports/$VERSION_DIR"
TOPOLOGIES_DIR="core_topologies"
SPEED=$1
MAXTIME=$2

TOPOLOGIES=('chaos.py')

#mkdir $CURR_PWD/$RESULTS_DIR 2> /dev/null #If folder exists, redirect error to sinkhole 
mkdir /tmp/$REPORTS_DIR 2> /dev/null #If folder exists, redirect error to sinkhole 
mkdir /tmp/$RESULTS_DIR 2> /dev/null #If folder exists, redirect error to sinkhole 
## Loops through all tmax sizes
for topo in "${TOPOLOGIES[@]}"
    do
    for tmax in "${TMAX[@]}"
    do
        for i in {1..1}
        do
            echo "Running eagp topology $topo with tmax $tmax" 
            $CURR_PWD/$TOPOLOGIES_DIR/$topo $tmax eagp3 $SPEED $MAXTIME &> /tmp/$RESULTS_DIR/$topo\_$tmax\_$i\_$DATA.log    
        done
    done
done

echo "Running gossip topology $topo" 
$CURR_PWD/$TOPOLOGIES_DIR/$topo 10 gossip $SPEED $MAXTIME &> /tmp/$RESULTS_DIR/$topo\_10\_1\_$DATA.log

echo "Running gossipfo topology $topo" 
$CURR_PWD/$TOPOLOGIES_DIR/$topo 10 gossipfo $SPEED $MAXTIME &> /tmp/$RESULTS_DIR/$topo\_10\_1\_$DATA.log

echo "Running mcfa topology $topo" 
$CURR_PWD/$TOPOLOGIES_DIR/$topo 10 mcfa $SPEED $MAXTIME &> /tmp/$RESULTS_DIR/$topo\_10\_1\_$DATA.log

echo "Running eagpd topology $topo  with tmax 10" 
$CURR_PWD/$TOPOLOGIES_DIR/$topo 10 eagpd $SPEED $MAXTIME &> /tmp/$RESULTS_DIR/$topo\_10\_1\_$DATA.log

cd $REPORTS_DIR
chown -R bcf:bcf *
cd ..

echo "Gerating reports"
$CURR_PWD/aux/report.py -a $CURR_PWD/$REPORTS_DIR 

#mv 2019* $CURR_PWD/$RESULTS_DIR
