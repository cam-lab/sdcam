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

//------------------------------------------------------------------------------
#include "video.h"

static auto lg = spdlog::basic_logger_mt("video   ", "log/vframe.log");

//------------------------------------------------------------------------------
void vstream_fun()
{
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    
    Socket sock(lg, SOCKET_IP, SRC_PORT);
    
    sock.set_recv_timeout(std::chrono::milliseconds(500));

    FrameReceiver frame_receiver(free_frame_q, incoming_frame_q, sock, lg);

    lg->info("begin incoming video stream processing");

    for(;;)
    {
        frame_receiver.recv();

        if(vsthread_exit.load())
        {
            lg->info("video stream processing exit notification received");
            break;
        }
    }
    lg->info("end video stream processing");
}
//------------------------------------------------------------------------------

