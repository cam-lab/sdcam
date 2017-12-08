
#ifndef VFRAME_H
#define VFRAME_H

#include <stdint.h>
#include <iostream>
#include <sstream>

#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>
    

#include <ip_qpipe_def.h>
#include <ip_qpipe_lib.h>

namespace bp = boost::python;
namespace np = boost::python::numpy;

const uint16_t FRAME_SIZE_X = 8; // 1280;
const uint16_t FRAME_SIZE_Y = 4; // 960;

const uint32_t RAWBUF_SIZE = 1280*960*2 + 4*1024;

//------------------------------------------------------------------------------
struct TVFrame
{
    TVFrame()
       : size_x(FRAME_SIZE_X)
       , size_y(FRAME_SIZE_Y)
       , pixbuf(np::empty(bp::make_tuple(FRAME_SIZE_Y, FRAME_SIZE_X), np::dtype::get_builtin<uint16_t>()))
       , rawbuf(np::empty(bp::make_tuple(RAWBUF_SIZE/sizeof(uint32_t)), np::dtype::get_builtin<uint32_t>()))
    {
    }
    
    bp::object pbuf() { return pixbuf; }
    
    uint32_t    size_x;
    uint32_t    size_y;
    np::ndarray pixbuf;
    np::ndarray rawbuf;
};
//------------------------------------------------------------------------------
#endif // VFRAME_H

