//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Frame Generator
//
//    Copyright (c) 2016-2017, 2024, Camlab Project Team
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
    TSocket sock(lg, SOCKET_IP, SRC_PORT);

    static uint16_t org = 0;

    uint16_t buf[FRAME_SIZE_Y][FRAME_SIZE_X];

    lg->info("begin frame stream generating");
    for(size_t i = 0; i < count; ++i)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(40));
        //TVFrame *f = free_frame_q.pop(std::chrono::milliseconds(1000));
        
        for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
        {
            for(size_t col = 0; col < FRAME_SIZE_X; ++col)
            {
                buf[row][col] = (org + row + col + 1) & VIDEO_OUT_DATA_MAX;
                if(row == 100 && col == 100) buf[row][col] = 1023;
                if(row == 100 && col == 101) buf[row][col] = 1023/2;
            }
        }

        org += 10;

        sock.write(reinterpret_cast<uint8_t*>(buf), FRAME_SIZE_X*FRAME_SIZE_Y);
    }
    lg->info("end frame stream generating");
    
    return 0;
}
//------------------------------------------------------------------------------

