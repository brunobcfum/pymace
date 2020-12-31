#!/bin/bash
TMAX=$1
CURR_PWD=$(pwd)
DATA=`date +%d_%m_%Y_%H_%M`
VERSION_DIR='OUROBOROS'
REPORTS_DIR='reports/'
RESULTS_DIR="reports/$VERSION_DIR"
TOPOLOGIES_DIR="core_topologies"
PROTOCOL=$2
SPEED=$3
TOPOLOGY='symmetrical.py'

mkdir /tmp/$REPORTS_DIR 2> /dev/null #If folder exists, redirect error to sinkhole 
mkdir /tmp/$RESULTS_DIR 2> /dev/null #If folder exists, redirect error to sinkhole 

for i in {1..5}
do
    echo "Running topology $TOPOLOGY with tmax $TMAX" 
    $CURR_PWD/$TOPOLOGIES_DIR/$TOPOLOGY $TMAX $PROTOCOL $SPEED 10000 &> /tmp/$RESULTS_DIR/$topo\_$tmax\_$i\_$DATA.log   
    DATA=`date +%d_%m_%Y_%H_%M`
done

cd $REPORTS_DIR
chown -R bcf:bcf *
cd ..

echo "Gerating reports"
$CURR_PWD/aux/report.py -a $CURR_PWD/$REPORTS_DIR 
