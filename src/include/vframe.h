//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Video Frame C/C++ module for Python
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

#ifndef VFRAME_H
#define VFRAME_H

#include <stdint.h>
#include <iostream>
#include <sstream>
#include <fstream>
#include <thread>
#include <chrono>
#include <atomic>

#if defined( __GNUG__ )
        
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#elif defined(_MSC_VER)

#pragma warning( push )  
#pragma warning( disable : 4100 )  //  warning C4100: unreferenced formal parameter
#pragma warning( disable : 4275 )  //  DLL related warning
#pragma warning( disable : 4251 )  //  DLL related warning
#pragma warning( disable : 4800 )  //  

#else

#error("E: unsupported compiler. Only GCC and MSVC are supported for now")

#endif //  __GNUC__

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

#include "utils.h"
#include "tsqueue.h"

namespace bp = boost::python;
namespace np = boost::python::numpy;

const uint32_t INP_PIX_W       = INPUT_PIXEL_WIDTH;
const uint32_t OUT_PIX_W       = OUTPUT_PIXEL_WIDTH;

const uint32_t INP_PIX_MAXVAL  = (1 << INP_PIX_W) - 1;
const uint32_t OUT_PIX_MAXVAL  = (1 << OUT_PIX_W) - 1;

const size_t   FRAME_POOL_SIZE = 4;

const uint16_t CFT_MASK        = 0x8000;
const uint16_t VST_MASK        = 0x4000;
const uint16_t FTT_MASK        = 0x2000;
const uint16_t LNUM_MASK       = (1 << 12) - 1;
const uint32_t MDBS_MASK       = ~(CFT_MASK | VST_MASK | FTT_MASK);

const uint16_t FRAME_MDB_SIZE  = 15;

const size_t   FNUM_SIZE       = 4;
const size_t   TSTUMP_SIZE     = 8;

//------------------------------------------------------------------------------
struct Vframe
{
    static const int FNUM_OFFSET     = 0;
    static const int TSTAMP_OFFSET   = FNUM_OFFSET   + 4;  // 16-bit words
    static const int SIZE_X_OFFSET   = TSTAMP_OFFSET + 8;
    static const int SIZE_Y_OFFSET   = SIZE_X_OFFSET + 1;
    static const int PIXWIDTH_OFFSET = SIZE_Y_OFFSET + 1;
    
    Vframe();
    
    bp::object pbuf() { return pixbuf; }

    Vframe  copy();
    
    void       retreive_fnum(uint16_t *p);
    void       retreive_tstamp(uint16_t *p);
    
    void       rshift(int n);
    void       divide(double n);
    
    uint32_t    fnum;
    uint64_t    tstamp;
    uint16_t    size_x;
    uint16_t    size_y;
    uint16_t    pixwidth;
    
    np::ndarray pixbuf;
};
//------------------------------------------------------------------------------
std::string vframe_str(Vframe & r);
std::string vframe_repr(Vframe & r);

using FrameQueue = tsqueue<Vframe *>;

extern std::thread      *vstream_thread;
extern std::atomic_bool  vsthread_exit;
extern FrameQueue        free_frame_q;
extern FrameQueue        incoming_frame_q;

void iframe_event_set();
void vstream_fun();

//------------------------------------------------------------------------------
#if defined( __GNUG__ )

#pragma GCC diagnostic pop

#elif defined(_MSC_VER)

#pragma warning( pop )  

#else

#error("E: unsupported compiler. Only GCC and MSVC are supported for now")

#endif //  __GNUC__

#endif // VFRAME_H
//------------------------------------------------------------------------------

