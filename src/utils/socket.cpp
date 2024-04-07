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

#include "socket.h"

//------------------------------------------------------------------------------
void TSocket::create(const char *a, uint16_t p)
{
    lg->info("create socket");
    fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    if(fd < 0)
    {
        throw TSocketException("cannot create socket", fd);
    }
    
    addr.sin_family      = AF_INET;
    addr.sin_addr.s_addr = inet_addr(a);
    addr.sin_port        = htons(p);

    lg->info("success, sockfd: {}", fd);
}
//------------------------------------------------------------------------------
void TSocket::bind()
{
    lg->info("try to bind socket {}:{}", addr.sin_addr.s_addr, ntohs(addr.sin_port));
    if(::bind(fd, reinterpret_cast<struct sockaddr *>(&addr), addrlen))
    {
        throw TSocketException("cannot bind socket", fd);
    }
    lg->info("socket bind successful");
}
//------------------------------------------------------------------------------
void TSocket::close()
{
    if(fd > 0)
    {
        ::close(fd);
        lg->info("close socket");
    }
    else
    {
        throw TSocketException("cannot close socket bacause socket descriptor has inconsistent value", fd);
    }
}
//------------------------------------------------------------------------------
int TSocket::read(uint8_t *buf, const size_t size)
{
    //lg->info("begin receiving");
    int             count;
    struct sockaddr raddr;
    socklen_t       raddrlen = sizeof(raddr);

    memset(&raddr, 0, raddrlen);

    count = recvfrom(fd, buf, size, 0, &raddr, &raddrlen);
    if(count < 0)
    {
        //lg->info("receive timeout expired");
    }
    else
    {
        //lg->info("received data count: {}", count);
    }

    return count;
}
//------------------------------------------------------------------------------
int TSocket::write(const uint8_t *src, const size_t size)
{
//  lg->info("sendto: sockfd: {}, buf: {}, count: {}", fd, fmt::ptr(src), size);
//  lg->info("sendto: addr: {:x}, port: {}", addr.sin_addr.s_addr, ntohs(addr.sin_port));

    return sendto(fd, src, size, 0, reinterpret_cast<struct sockaddr *>(&addr), addrlen);
}
//------------------------------------------------------------------------------
void TSocket::set_recv_timeout(const std::chrono::milliseconds timeout)
{
    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = timeout.count()*1000;
    if (setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO,&tv,sizeof(tv)) < 0)
    {
        throw TSocketException("cannot set timeout for socket", fd);
    }
    lg->info("set timeout: {} ms for receiving data from the socket", timeout.count());
}
//------------------------------------------------------------------------------

