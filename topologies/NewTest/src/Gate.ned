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

package newtest;

import inet.applications.contract.IApp;

simple Gate like IApp
{
    parameters:
        // string interfaceTableModule;   // The path to the InterfaceTable module
        // interfaceTableModule = default("^.interfaceTable");
        //string role;   // The node's role. Server or Client?
        //int localPort;  // local port to listen on
        @display("i=block/app");
        @lifecycleSupport;
        //double stopOperationExtraTime @unit(s) = default(-1s);    // extra time after lifecycle stop operation finished
        //double stopOperationTimeout @unit(s) = default(2s);    // timeout value for lifecycle stop operation
        //@signal[packetSent](type=inet::Packet);
        //@statistic[echoedPk](title="packets echoed"; source=packetSent; record=count,"sum(packetBytes)","vector(packetBytes)"; interpolationmode=none);
    gates:
        input socketIn @labels();
        output socketOut @labels();

}
