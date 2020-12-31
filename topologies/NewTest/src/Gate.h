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

#ifndef GATE_H_
#define GATE_H_

#include "inet/applications/base/ApplicationBase.h"

#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <termios.h>
#include <unistd.h>
#include <iostream>
#include <vector>
#include <cstdlib>
#include <thread>
#include <chrono>

using namespace omnetpp;
using namespace inet;

class Gate : public cSimpleModule {
public:
    Gate();
    virtual ~Gate();
protected:
    virtual void initialize(int stage) override;
    virtual void finish() override;
    virtual void processStart();
    static void threadCall(Gate *obj);
};



#endif /* GATE_H_ */
