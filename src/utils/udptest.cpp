//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: UDP Load Test
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

#if defined( __GNUG__ )
        
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#pragma GCC diagnostic pop

#elif defined(_MSC_VER)

#pragma warning( push )  
#pragma warning( disable : 4100 )  //  warning C4100: unreferenced formal parameter
#pragma warning( disable : 4275 )  //  DLL related warning
#pragma warning( disable : 4251 )  //  DLL related warning
#pragma warning( disable : 4800 )  //  
#pragma warning( disable : 4267 )  //  
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#pragma warning( pop )  

#pragma warning( disable : 4244 )  //  

#else

#error("E: unsupported compiler. Only GCC and MSVC are supported for now")

#endif //  __GNUC__

#include <vframe.h>

#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>

#include <socket.h>
#include <vframe.h>
#include <progressbar.h>

const char     *SOCKET_IP   = "192.168.10.10";
const uint16_t  SRC_PORT = 50000;
const uint16_t  DST_PORT = 50000;

//------------------------------------------------------------------------------

static auto lg = spdlog::basic_logger_mt("udptest", "log/udptest.log");

void udp_tx(size_t count);

//------------------------------------------------------------------------------
int main(int argc, char *argv[])
{
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    
    if(argc > 2)
    {
        print("E: too many arguments, supports ony one: packet count");
        return -1;
    }
    
    size_t pkt_count = 1;
    if(argc == 2)
    {
        pkt_count = std::stoi(argv[1]);
    }

    try
    {
        print("------------------------------------");
        print("begin packet stream generating for {} packets\n", pkt_count);
        //auto pkt_num = fgen(frame_count);
        udp_tx(pkt_count);
        //print("\nend frame stream generating, {} packets sent", pkt_num);
        print("------------------------------------");

    }
    catch(SocketException e)
    {
        lg->error("{}, socket fd: {}", e.msg, e.fd);
        return -1;
    }
    
    return 0;
}
//------------------------------------------------------------------------------
void udp_tx(size_t count)
{
    Socket sock(lg, SOCKET_IP, SRC_PORT, false);

    uint16_t idx  = 0;
    uint32_t pnum = 0;

    const uint16_t LAN_AGENT_IDX  = 0;
    const size_t PKT_PAYLOAD_SIZE = 16; // 1472/2;

    std::array<uint16_t, PKT_PAYLOAD_SIZE> buf;

    for(size_t p = 0; p < count; ++p)
    {
        buf[idx++] = LAN_AGENT_IDX;
        buf[idx++] = ++pnum;
        buf[idx++] = pnum >> 16;
        
        for(size_t i = idx; i < PKT_PAYLOAD_SIZE; ++i)
        {
            buf[i] = ((pnum+(i-idx)*2) & 0xff) + ((pnum+(i-idx)*2+1) << 8);
        }
        idx = 0;
        
        sock.write(reinterpret_cast<uint8_t *>(buf.data()), PKT_PAYLOAD_SIZE*2);
    }

//------------------------------------------------------------------------------
void dump(uint8_t *p, size_t size)
{
    for(size_t i = 0; i < size; ++i)
    {
        if( i%16 == 0)
        {
            fmt::print("\n");
            fmt::print("{:04x}: ", i);
        }

        fmt::print("{:02x} ", p[i]);
        if( (i+1)%8 == 0)
        {
            fmt::print(" ");
        }
    }
    fmt::print("\n");
}
//------------------------------------------------------------------------------

