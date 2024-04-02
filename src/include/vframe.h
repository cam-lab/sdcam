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

const uint32_t RAWBUF_SIZE = FRAME_SIZE_X*FRAME_SIZE_Y*2 + 2*1024;

const uint32_t HOST_METABUF_SIZE    = 4 + 1024;


const uint32_t VDATA_INP_W   = VIDEO_DATA_INP_WIDTH;
const uint32_t VDATA_OUT_W   = VIDEO_DATA_OUT_WIDTH;

const uint32_t VDATA_INP_MAX = (1 << VDATA_INP_W) - 1;
const uint32_t VDATA_OUT_MAX = (1 << VDATA_OUT_W) - 1;

const size_t FRAME_POOL_SIZE = 4;

//------------------------------------------------------------------------------
struct TVFrame
{
    static const int META_INFO_HEADER_OFFSET = 10;          // 32-bit words
    static const int META_INFO_DATA_OFFSET   = 14;  
           
    static const int TSTAMP_OFFSET           = 4;                  // 16-bit words
    static const int SIZE_X_OFFSET           = TSTAMP_OFFSET + 8;
    static const int SIZE_Y_OFFSET           = SIZE_X_OFFSET + 1;
    static const int PIXWIDTH_OFFSET         = SIZE_Y_OFFSET + 1;
                                             
    static const int DET_CR_OFFSET           = PIXWIDTH_OFFSET + 1; 
    static const int DET_IEXP_OFFSET         = DET_CR_OFFSET   + 1; 
    static const int DET_FEXP_OFFSET         = DET_IEXP_OFFSET + 1; 
    static const int DET_PGA_CODE_OFFSET     = DET_FEXP_OFFSET + 1; 

    static const int NPULSES_OFFSET          = DET_PGA_CODE_OFFSET + 1; 
    static const int PINCH_OFFSET            = NPULSES_OFFSET      + 1; 
    static const int DEPTH_OFFSET            = PINCH_OFFSET        + 1; 
    static const int TRIM_OFFSET             = DEPTH_OFFSET        + 1; 
                                                                   
    static const int PWIDTH_OFFSET           = TRIM_OFFSET         + 1; 
    
    TVFrame();
    
    bp::object pbuf() { return pixbuf; }

    TVFrame  copy();
    bool     fill(uint8_t *src, uint32_t len);
    
    uint32_t retreive_fnum(uint16_t *p);
    uint64_t retreive_tstamp(uint16_t *p);
    
    char      *raw_buf()     const { return rawbuf.get_data(); }
    uint32_t   raw_buf_len() const { return rawbuf.shape(0); }
    
    void       rshift(int n);
    void       divide(double n);
    
    
    uint32_t    host_fnum;
    uint32_t    host_fpixsize;
    uint32_t    host_fsize_x;
    uint32_t    host_fsize_y;
    
    uint32_t    meta_buf_size;
    uint32_t    meta_elem_size;
    uint32_t    meta_info_size;
    
    uint32_t    fnum;
    uint64_t    tstamp;
    uint16_t    size_x;
    uint16_t    size_y;
    uint16_t    pixwidth;

    uint16_t    det_cr;
    uint16_t    det_iexp;
    uint16_t    det_fexp;
    uint16_t    det_pga_code;

    uint16_t    npulses;
    uint16_t    pinch;
    uint16_t    depth;
    uint16_t    trim;

    uint16_t    pwidth;
    
    
    np::ndarray pixbuf;
    np::ndarray rawbuf;
};
//------------------------------------------------------------------------------
inline bool deserialize_frame(void *frameObj, uint8_t *src, uint32_t len)
{
    return static_cast<TVFrame *>(frameObj)->fill(src, len);
}
//------------------------------------------------------------------------------
std::string vframe_str(TVFrame & r);
std::string vframe_repr(TVFrame & r);

extern std::thread        *vstream_thread;
extern std::atomic_bool    vsthread_exit;
extern tsqueue<TVFrame *>  free_frame_q;
extern tsqueue<TVFrame *>  incoming_frame_q;

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

