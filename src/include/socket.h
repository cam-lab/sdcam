//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: UDP Socket
//
//    Copyright (c) 2024, Camlab Project Team
//
//    Permission is hereby granted, free of charge, to any person
//    obtaining  a copy of this software and associated documentation
//    files (the "Software"), to deal in the Software without restriction,
//    including without limitation the rights to use, copy, modify, merge,
//    publish, distribute, sublicense, and/or sell copies of the Software,
//    and to permit persons to whom the Software is furnished to do so,
//    subject to the following conditions:
//
//    The above copyright notice and this permission notice shall be included
//    in all copies or substantial portions of the Software.
//
//    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
//    EXPRESS  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
//    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
//    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
//    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
//    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
//    THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//
//-------------------------------------------------------------------------------


#ifndef SOCKET_API_H
#define SOCKET_API_H

#include <iomanip>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <net/ethernet.h>

#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>

const size_t MIN_ETH_PACKET_SIZE    = 40;
const size_t BUF_SIZE               = 2048;

//------------------------------------------------------------------------------
struct TSocketException
{
    TSocketException(std::string s, int sd) : msg(s), fd(sd) { }

    std::string msg;
    int         fd;
};
//------------------------------------------------------------------------------
class TSocket
{
public:
    TSocket(std::shared_ptr<spdlog::logger> logger,
            const char *a, uint16_t p)
        : lg(logger)
        , fd(0)
        , addr{0, 0, 0, { } }
        , addrlen(sizeof(addr))
        
    {
        create();
        bind(a, p);
    }
    ~TSocket() { if(fd) close(); }


    void create();
    void bind  (const char *addr, uint16_t port);
    void close ();
    int  read  (      uint8_t *dst, const size_t size);
    int  write (const uint8_t *src, const size_t size);

private:
    std::shared_ptr<spdlog::logger> lg;
    int                             fd;
    struct sockaddr_in              addr;
    socklen_t                       addrlen;
};
//------------------------------------------------------------------------------
#endif // SOCKET_API_H
//------------------------------------------------------------------------------

