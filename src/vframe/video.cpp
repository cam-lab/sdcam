//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Processing video
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

//------------------------------------------------------------------------------
#include "vframe.h"

//------------------------------------------------------------------------------
void vstream_fun()
{
    static uint16_t org = 0;

    uint16_t buf[FRAME_SIZE_Y][FRAME_SIZE_X];

    print("video: INFO: begin incoming video stream processing");
    for(;;)
    {
        std::this_thread::sleep_for(std::chrono::milliseconds(40));
        TVFrame *f = free_frame_q.pop(std::chrono::milliseconds(1000));
        
        if(f)
        {
            for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
            {
                for(size_t col = 0; col < FRAME_SIZE_X; ++col)
                {
                    buf[row][col] = (org + row + col + 1) & VIDEO_OUT_DATA_MAX;
                    if(row == 100 && col == 100) buf[row][col] = 1023;
                    if(row == 100 && col == 101) buf[row][col] = 1023/2;
                }
            }

            std::memcpy(f->pixbuf.get_data(),
                        reinterpret_cast<uint8_t*>(buf),
                        FRAME_SIZE_X*FRAME_SIZE_Y*sizeof(buf[0][0]));

            org += 10;

            incoming_frame_q.push(f);
            iframe_event_set();
        }
        
        if(vsthread_exit.load())
        {
            print("video: INFO: video stream processing exit notification received");
            break;
        }
    }
    print("video: INFO: end video stream processing");
}
//------------------------------------------------------------------------------

