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


#include <vector>
#include <socket.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/basic_file_sink.h>

#include <progressbar.h>
#include <vframe.h>

const char     *SOCKET_IP      = "192.168.10.1";
const char     *DEV_IP         = "192.168.10.10";
const uint16_t  SRC_PORT       = 50000;
const uint16_t  DST_PORT       = 50000;
const size_t    PKT_SIZE       = 2048;
const uint16_t  LAN_AGENT_IDX  = 0;

using SockBuf = std::array<uint16_t, PKT_SIZE/sizeof(uint16_t)>;

//------------------------------------------------------------------------------

static auto lg = spdlog::basic_logger_mt("udptest", "log/udptest.log");

void udp_tx(size_t count);
void udp_rx(size_t send_pkt_count);
void dump(uint8_t *p, size_t size);

std::atomic_bool udp_rx_thread_start;
std::atomic_bool udp_rx_thread_socket_fail;
//------------------------------------------------------------------------------
int main(int argc, char *argv[])
{
    lg->flush_on(spdlog::level::debug);
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    lg->info("-------------------------");
    
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
        udp_rx_thread_start.store(false);
        udp_rx_thread_socket_fail.store(false);
        auto rx_thread = new std::thread(udp_rx, pkt_count);
        while(!udp_rx_thread_start)
        {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            if(udp_rx_thread_socket_fail)
            {
                rx_thread->join();
                return -1;
            }
        }
        
        print("begin packet stream generating for {} packets\n", pkt_count);
        udp_tx(pkt_count);

        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        udp_rx_thread_start.store(false);
        rx_thread->join();
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
    
    const size_t chunk_size = count < 100 ? 1 : count/100; // 1%

    const size_t PKT_PAYLOAD_SIZE = 1472/2;

    SockBuf buf;
    struct sockaddr_in dst_addr;
    
    ProgressBar progress{std::clog, 100u, "Packets:", '#'};
    
    dst_addr.sin_family      = AF_INET;
    dst_addr.sin_addr.s_addr = inet_addr(DEV_IP);
    dst_addr.sin_port        = htons(DST_PORT);

    uint64_t total_size      = 0;
    auto tpoint_before       = std::chrono::high_resolution_clock::now();

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

        sock.write(dst_addr, reinterpret_cast<uint8_t *>(buf.data()), PKT_PAYLOAD_SIZE*2);
        if(sock.get_tx_buf_level() > 1024*1024*2)
        {
            std::this_thread::sleep_for(std::chrono::microseconds(10000));
        }

        total_size += PKT_PAYLOAD_SIZE*2;

        if(p%chunk_size == 0)
        {
            double num = p;
            progress.write(num/count);
        }
    }
    while(true)
    {
        if(!sock.get_tx_buf_level()) break;
    }
    auto tpoint_after = std::chrono::high_resolution_clock::now();
    progress.write(1);
    
    auto dtime = tpoint_after - tpoint_before;
    
    auto speed = total_size*8e3/std::chrono::duration_cast<std::chrono::nanoseconds>(dtime).count();
    
    print("\nTx speed: {:3.3f} Mpbs, total size: {} bytes", speed, total_size);
}
//------------------------------------------------------------------------------
void udp_rx(size_t send_pkt_count)
{
    try
    {
        Socket sock(lg, SOCKET_IP, DST_PORT);

        sock.set_recv_timeout(std::chrono::milliseconds(500));

        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        udp_rx_thread_start.store(true);
        lg->info("create and bind Rx socket");

        size_t   pkt_count           = 0;
        size_t   incorrect_pkt_count = 0;

        std::vector<bool> ids(send_pkt_count);
        
        for(auto i : ids)
        {
            i = false;
        }
        ids[0] = true;
        
        uint64_t total_size = 0;
        std::chrono::time_point<std::chrono::high_resolution_clock> tpoint_begin;
        std::chrono::time_point<std::chrono::high_resolution_clock> tpoint_end;
        bool begin = false;
        for(;;)
        {
            int     count;
            uint8_t rxbuf[PKT_SIZE];
            
            count = sock.read(rxbuf, PKT_SIZE);
            
            if(count >= 0)
            {
                if( !begin )
                {
                    begin = true;
                    tpoint_begin = std::chrono::high_resolution_clock::now();
                }
                tpoint_end = std::chrono::high_resolution_clock::now();
                total_size += count;
                
                uint16_t idx = rxbuf[0] + (rxbuf[1] << 8);
                uint32_t id  = rxbuf[2] + (rxbuf[3] << 8) + (rxbuf[4] << 16) + (rxbuf[5] << 24);

                if(idx != LAN_AGENT_IDX)
                {
                    lg->error("rx: packet id: {}, invalid index field {}, must be {}", id, idx, LAN_AGENT_IDX);
                    continue;
                }

                ids[id] = true;
                
                size_t cnt = count;
                for(size_t i = 6; i < cnt; ++i)
                {
                    uint8_t exp = id + i - 6;
                    if(rxbuf[i] != exp)
                    {
                        lg->error("rx: packet data at {} mismatch: expected {:x}, actual {:x}", i, exp, rxbuf[i]);
                        dump(rxbuf, count);
                        ++incorrect_pkt_count;
                        break;
                    }
                }

                ++pkt_count;
            }
            
            if(!udp_rx_thread_start)
            {
                auto dtime = tpoint_end - tpoint_begin;

                auto speed = total_size*8e3/std::chrono::duration_cast<std::chrono::nanoseconds>(dtime).count();
                
                size_t lost_pkt_count = 0;
                for(auto i : ids)
                {
                    if( !i )
                    {
                        ++lost_pkt_count;
                    }
                }

                print("\nRx speed: {:3.3f} Mpbs, total size: {} bytes, Rx time elapsed: {} ms",
                      speed, total_size, std::chrono::duration_cast<std::chrono::milliseconds>(dtime).count());

                print("received packet count:  {}", pkt_count);
                print("lost packet count:      {}", lost_pkt_count);
                print("incorrect packet count: {}", incorrect_pkt_count);
                return;
            }
        }
    }
    catch(SocketException e)
    {
        lg->error("{}, socket fd: {}", e.msg, e.fd);
        udp_rx_thread_socket_fail.store(true);
        return;
    }
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

