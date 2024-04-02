//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Frame Generator
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

#include "socket.h"
#include "vframe.h"

const char     *SOCKET_IP   = "127.0.0.1";
const uint16_t  SRC_PORT = 50000;
const uint16_t  DST_PORT = 50001;

//------------------------------------------------------------------------------

static auto lg = spdlog::basic_logger_mt("framegen", "log/vframe.log");

int fgen(const size_t count);


//------------------------------------------------------------------------------
int main()
{
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    
    try
    {
        return fgen(1);
    }
    catch(TSocketException e)
    {
        lg->error("{}, socket fd: {}", e.msg, e.fd);
        return -1;
    }
}
//------------------------------------------------------------------------------
int fgen(const size_t count)
{
    lg->info("------------------------------------");
    TSocket sock(lg, SOCKET_IP, SRC_PORT, false);

    static uint32_t fnum = 0x12345678;
    static uint16_t org  = 0;
    
    //const size_t PKT_PAYLOAD_SIZE = 1472/2;
    const size_t PKT_PAYLOAD_SIZE = 90/2;
    
    std::array<uint16_t, PKT_PAYLOAD_SIZE> buf;

    uint16_t fpool[FRAME_SIZE_Y][FRAME_SIZE_X];

    lg->info("begin frame stream generating");
    for(size_t i = 0; i < count; ++i)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(40));
        //TVFrame *f = free_frame_q.pop(std::chrono::milliseconds(1000));
        
        for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
        {
            for(size_t col = 0; col < FRAME_SIZE_X; ++col)
            {
                fpool[row][col] = (org + row + col + 1) & OUT_PIX_MAXVAL;
                if(row == 100 && col == 100) fpool[row][col] = 1023;
                if(row == 100 && col == 101) fpool[row][col] = 1023/2;
            }
        }

        org += 10;
        
        // frame number
        ++fnum;

        // timestamp
        auto now    = std::chrono::high_resolution_clock::now();
        auto epoch  = now.time_since_epoch();
        uint64_t tstamp = std::chrono::duration_cast<std::chrono::nanoseconds>(epoch).count()/10;
        
        print("timestamp: {:x}", tstamp);

        // send frame
        size_t idx     = 0;
        size_t pkt_num = 0;
        
        auto put_data = [&](uint16_t data)
        {
            buf[idx++] = data;
            if(idx == PKT_PAYLOAD_SIZE)
            {
                sock.write(reinterpret_cast<uint8_t*>(buf.data()), idx*2);
                print("send pkt {}, count: {}", ++pkt_num, idx);
                idx = 0;
            }
        };

        buf[idx++] = CFT_MASK;
        buf[idx++] = VFT_MASK + FRAME_MDB_SIZE;

        buf[idx++] = (fnum >> 0)  & 0xff;
        buf[idx++] = (fnum >> 8)  & 0xff;
        buf[idx++] = (fnum >> 16) & 0xff;
        buf[idx++] = (fnum >> 24) & 0xff;
        
        buf[idx++] = (tstamp >> 0)  & 0xff;
        buf[idx++] = (tstamp >> 8)  & 0xff;
        buf[idx++] = (tstamp >> 16) & 0xff;
        buf[idx++] = (tstamp >> 24) & 0xff;
        buf[idx++] = (tstamp >> 32) & 0xff;
        buf[idx++] = (tstamp >> 40) & 0xff;
        buf[idx++] = (tstamp >> 48) & 0xff;
        buf[idx++] = (tstamp >> 56) & 0xff;
        
        buf[idx++] = FRAME_SIZE_X;
        buf[idx++] = FRAME_SIZE_Y;
        buf[idx++] = INP_PIX_W;

        for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
        {
            put_data(VFT_MASK + FTT_MASK + 1);
            put_data(row & LNUM_MASK);

            for(size_t col = 0; col < FRAME_SIZE_X; ++col)
            {
                print("row: {}, col: {}, val: {}, idx: {}", row, col, fpool[row][col], idx);
                put_data(fpool[row][col]);
            }
        }
        sock.write(reinterpret_cast<uint8_t*>(buf.data()), idx*2);
        print("send last pkt, pkt_num {}, count: {}", ++pkt_num, idx);

    }
    lg->info("end frame stream generating");

    return 0;
}
//------------------------------------------------------------------------------

