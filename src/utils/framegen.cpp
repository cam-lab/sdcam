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

#include <socket.h>
#include <vframe.h>
#include <progressbar.h>

const char     *SOCKET_IP   = "127.0.0.1";
const char     *DST_IP      = "127.0.0.1";
const uint16_t  SRC_PORT = 50000;
const uint16_t  DST_PORT = 50000;

//------------------------------------------------------------------------------

static auto lg = spdlog::basic_logger_mt("framegen", "log/vframe.log");

int fgen(const size_t count);


//------------------------------------------------------------------------------
int main(int argc, char *argv[])
{
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    
    if(argc > 2)
    {
        print("E: too many arguments, supports ony one: frame count");
        return -1;
    }
    
    size_t frame_count = 10000;
    if(argc == 2)
    {
        frame_count = std::stoi(argv[1]);
    }

    try
    {
        print("------------------------------------");
        print("begin frame stream generating for {} frames\n", frame_count);
        auto pkt_num = fgen(frame_count);
        print("\nend frame stream generating, {} packets sent", pkt_num);
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
int fgen(const size_t frame_count)
{
    Socket sock(lg, SOCKET_IP, SRC_PORT, false);

    static uint32_t fnum = 0;
    static uint16_t org  = 0;
    
    const size_t PKT_PAYLOAD_SIZE = 1472/2;
    
    std::array<uint16_t, PKT_PAYLOAD_SIZE> buf;

    uint16_t fpool[FRAME_SIZE_Y][FRAME_SIZE_X];

    const size_t chunk_size = frame_count < 100 ? 1 : frame_count/100; // 1%
    
    struct sockaddr_in dst_addr;

    dst_addr.sin_family      = AF_INET;
    dst_addr.sin_addr.s_addr = inet_addr(DST_IP);
    dst_addr.sin_port        = htons(DST_PORT);


    ProgressBar progress{std::clog, 100u, "Frames:", '#'};

    size_t pkt_num     = 0;
    auto tpoint_before = std::chrono::high_resolution_clock::now();
    auto tpoint_after  = std::chrono::high_resolution_clock::now();
    
    for(size_t i = 0; i < frame_count; ++i)
    {
        auto dtime = std::chrono::milliseconds(40) - (tpoint_after - tpoint_before);
        
        std::this_thread::sleep_for(dtime);
        
        tpoint_before = std::chrono::high_resolution_clock::now();
        
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
        
        ++fnum;

        // timestamp
        auto now        = std::chrono::high_resolution_clock::now();
        auto epoch      = now.time_since_epoch();
        uint64_t tstamp = std::chrono::duration_cast<std::chrono::nanoseconds>(epoch).count()/10;
        
        // send frame
        size_t idx     = 0;
        
        auto put_data = [&](uint16_t data)
        {
            buf[idx++] = data;
            if(idx == PKT_PAYLOAD_SIZE)
            {
                sock.write(dst_addr, reinterpret_cast<uint8_t *>(buf.data()), idx*2);
                ++pkt_num;
                idx = 0;
            }
        };

        buf[idx++] = CFT_MASK;
        buf[idx++] = VST_MASK + FRAME_MDB_SIZE;

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
            put_data(VST_MASK + FTT_MASK + 1);
            put_data(row & LNUM_MASK);

            for(size_t col = 0; col < FRAME_SIZE_X; ++col)
            {
                put_data(fpool[row][col]);
            }
        }

        sock.write(dst_addr, reinterpret_cast<uint8_t *>(buf.data()), idx*2);

        if(fnum%chunk_size == 0)
        {
            double frame_num = fnum;
            progress.write(frame_num/frame_count);
        }
        
        tpoint_after  = std::chrono::high_resolution_clock::now();

    }

    return pkt_num;
}
//------------------------------------------------------------------------------

