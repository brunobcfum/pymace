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
#define PORT 56888

#include "Gate.h"
#include "inet/common/ModuleAccess.h"
#include <omnetpp.h>

Define_Module(Gate);

Gate::Gate() {
    // TODO Auto-generated constructor stub

}

void Gate::initialize(int stage)
{
    //ApplicationBase::initialize(stage);
    if (stage == INITSTAGE_LOCAL) {
        EV << "Initializing node: " << getParentModule()->getName() << endl;
    }
    scheduleStart(1);
    std::thread AThread(&Gate::threadCall, this);
    AThread.detach();
}

void Gate::processStart() {
    EV << "Starting node: " << getParentModule()->getName() << endl;
}


void Gate::finish()
{
    //ApplicationBase::finish();
}

void Gate::threadCall(Gate *obj) {
    std::string node = obj->getParentModule()->getName();
    std::string nodeNumber = node.substr(node.length()-1, 1);
    OPP_LOGPROXY(&obj, omnetpp::LOGLEVEL_INFO, nullptr).getStream() << "Starting thread: " << nodeNumber << endl;
    int server_fd, new_socket, valread;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    char buffer[1024] = {0};
    //char *hello = "Hello from server";

    // Creating socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0)
    {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT,
                                                  &opt, sizeof(opt)))
    {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons( PORT+std::stoi(nodeNumber) );

    // Forcefully attaching socket to the port 8080
    if (bind(server_fd, (struct sockaddr *)&address,
                                 sizeof(address))<0)
    {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, 3) < 0)
    {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    if ((new_socket = accept(server_fd, (struct sockaddr *)&address,
                       (socklen_t*)&addrlen))<0)
    {
        perror("accept");
        exit(EXIT_FAILURE);
    }
    valread = read( new_socket , buffer, 5);
    if ( strcmp(buffer,"bruno") == 0 ) {
        printf("%s\n",buffer );
        OPP_LOGPROXY(&obj, omnetpp::LOGLEVEL_INFO, nullptr).getStream() << buffer << endl;
        obj->finish();
    }

    //send(new_socket , hello , strlen(hello) , 0 );

    //obj->scheduleAt(10, msg);

}


Gate::~Gate() {
    // TODO Auto-generated destructor stub
}

