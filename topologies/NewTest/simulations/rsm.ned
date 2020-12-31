//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package newtest.simulations;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.AdhocHost;
import inet.physicallayer.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.physicallayer.unitdisk.UnitDiskRadioMedium;
import inet.visualizer.contract.IIntegratedVisualizer;
import inet.mobility.contract.IMobility;

network Manet
{
    parameters:
        @display("bgb=650,450");

    submodules:
        visualizer: <default("IntegratedCanvasVisualizer")> like IIntegratedVisualizer if hasVisualizer() {
            parameters:
                @display("p=43,87;is=s");
        }

        configurator: Ipv4NetworkConfigurator {
            parameters:
                //config = xmldoc("config.xml");
                @display("p=43,157;is=s");
        }

        //radioMedium: UnitDiskRadioMedium {
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=42,31;is=s");
                //ignorePartialInterference = true;
        }

        drone0: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,50;bgu=m");
        }
        drone1: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,50;bgu=m");
        }
        drone2: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,150;bgu=m");
        }
        drone3: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,150;bgu=m");
        }
        drone4: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,250;bgu=m");
        }
        drone5: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=450,250;bgu=m");
        }
        drone6: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,350;bgu=m");
        }
        drone7: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=450,350;bgu=m");
        }
        drone8: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,150;bgu=m");
        }
        drone9: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,250;bgu=m");
        }
}

network SymManet
{
    parameters:
        @display("bgb=650,450");

    submodules:
        visualizer: <default("IntegratedCanvasVisualizer")> like IIntegratedVisualizer if hasVisualizer() {
            parameters:
                @display("p=43,87;is=s");
        }

        configurator: Ipv4NetworkConfigurator {
            parameters:
                //config = xmldoc("config.xml");
                @display("p=43,157;is=s");
        }

        //radioMedium: UnitDiskRadioMedium {
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=42,31;is=s");
        }

        drone0: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,50");
        }
        drone1: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,50");
        }
        drone2: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,150");
        }
        drone3: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,150");
        }
        drone4: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,250");
        }
        drone5: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,250");
        }
        drone6: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,50");
        }
        drone7: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,250");
        }
        drone8: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,150");
        }
}

network DenseManet
{
    parameters:
        @display("bgb=650,450");

    submodules:
        visualizer: <default("IntegratedCanvasVisualizer")> like IIntegratedVisualizer if hasVisualizer() {
            parameters:
                @display("p=43,87;is=s");
        }

        configurator: Ipv4NetworkConfigurator {
            parameters:
                //config = xmldoc("config.xml");
                @display("p=43,157;is=s");
        }

        //radioMedium: UnitDiskRadioMedium {
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=42,31;is=s");
        }

        drone0: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,50");
        }
        drone1: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,50");
        }
        drone2: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,150");
        }
        drone3: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,150");
        }
        drone4: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,250");
        }
        drone5: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=250,250");
        }
        drone6: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,50");
        }
        drone7: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=150,250");
        }
        drone8: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=350,150");
        }
        drone9: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=302,203");
        }
        drone10: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=408,319");
        }
        drone11: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=408,203");
        }
        drone12: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/drone;p=302,319");
        }
}

network Eagp
{
    parameters:
        @display("bgb=650,450");

    submodules:
        visualizer: <default("IntegratedCanvasVisualizer")> like IIntegratedVisualizer if hasVisualizer() {
            parameters:
                @display("p=43,87;is=s");
        }

        configurator: Ipv4NetworkConfigurator {
            parameters:
                //config = xmldoc("config.xml");
                @display("p=43,157;is=s");
        }

        //radioMedium: UnitDiskRadioMedium {
        radioMedium: Ieee80211ScalarRadioMedium {
            parameters:
                @display("p=42,31;is=s");
                //ignorePartialInterference = true;
        }

        node0: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=150,50;bgu=m");
        }
        node1: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=250,50;bgu=m");
        }
        node2: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=150,150;bgu=m");
        }
        node3: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=250,150;bgu=m");
        }
        node4: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=350,250;bgu=m");
        }
        node5: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=450,250;bgu=m");
        }
        node6: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=350,350;bgu=m");
        }
        node7: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=450,350;bgu=m");
        }
        node8: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=350,150;bgu=m");
        }
        node9: AdhocHost {
            parameters:
                @display("r=100,,#707070;i=misc/node;p=250,250;bgu=m");
        }
}
