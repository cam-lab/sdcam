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

#include "timing.h"
#include "vframe.h"

#include <array_ref.h>
#include <array_indexing_suite.h>

//------------------------------------------------------------------------------
TVFrame          *frame_pool;
std::thread      *vstream_thread;
std::atomic_bool  vsthread_exit;
FrameQueue        free_frame_q("free_q");
FrameQueue        incoming_frame_q("incoming_q");

bp::object        inpframe_event;
bp::object        vsthread_finish_event;

auto lg = spdlog::basic_logger_mt("vframe  ", "log/vframe.log", true);

//------------------------------------------------------------------------------
void init_numpy()
{
    np::initialize();
}
//------------------------------------------------------------------------------
void create_frame_pool()
{
    lg->set_pattern("%Y-%m-%d %H:%M:%S %n   %L : %v");
    spdlog::flush_on(spdlog::level::info);

    frame_pool = new TVFrame[FRAME_POOL_SIZE];
    lg->info("create video frame pool");
}
//------------------------------------------------------------------------------
void delete_frame_pool()
{
    delete[] frame_pool;
    lg->info("delete video frame pool");
}
//------------------------------------------------------------------------------
TVFrame::TVFrame()
    : fnum           ( 0 )
    , tstamp         ( 0 )
    , size_x         ( 0 )
    , size_y         ( 0 )
    , pixwidth       ( 0 )
    , pixbuf(np::empty(bp::make_tuple(FRAME_SIZE_Y, FRAME_SIZE_X), np::dtype::get_builtin<uint16_t>()))
{
}
//------------------------------------------------------------------------------
TVFrame TVFrame::copy()
{
    TVFrame f = *this;
    
    f.pixbuf = pixbuf.copy();
    
    return f;
}
//------------------------------------------------------------------------------
void TVFrame::retreive_fnum(uint16_t *p)
{
    fnum = (  p[0] & 0xff)        +
           ( (p[1] & 0xff) << 8)  +
           ( (p[2] & 0xff) << 16) +
           ( (p[3] & 0xff) << 24);

    return;
}
//------------------------------------------------------------------------------
void TVFrame::retreive_tstamp(uint16_t *p)
{
    tstamp = ( static_cast<uint64_t>(p[0] & 0xff)     )  +
             ( static_cast<uint64_t>(p[1] & 0xff) << 8)  +
             ( static_cast<uint64_t>(p[2] & 0xff) << 16) +
             ( static_cast<uint64_t>(p[3] & 0xff) << 24) +
             ( static_cast<uint64_t>(p[4] & 0xff) << 32) +
             ( static_cast<uint64_t>(p[5] & 0xff) << 40) +
             ( static_cast<uint64_t>(p[6] & 0xff) << 48) +
             ( static_cast<uint64_t>(p[7] & 0xff) << 56);

    return;
}
//------------------------------------------------------------------------------
//#pragma GCC push_options
//#pragma GCC optimize ("unroll-lools")

void TVFrame::rshift(int n)
{
    uint16_t *buf = reinterpret_cast<uint16_t *>(pixbuf.get_data());
    
    for(int i = 0; i < FRAME_SIZE_X*FRAME_SIZE_Y; ++i)
    {
        buf[i] >>= n;
    }
}
//------------------------------------------------------------------------------
void TVFrame::divide(double n)
{
    uint16_t *buf = reinterpret_cast<uint16_t *>(pixbuf.get_data());
    
    for(int i = 0; i < FRAME_SIZE_X*FRAME_SIZE_Y; ++i)
    {
        buf[i] /= n;
    }
}
//------------------------------------------------------------------------------
std::string vframe_str(TVFrame & r)
{
    std::stringstream out;

    out << "    fnum          : " << r.fnum     << "\n";
    out << "    size_x        : " << r.size_x   << "\n";
    out << "    size_y        : " << r.size_y   << "\n";
    out << "    pixwidth      : " << r.pixwidth << std::endl;

    return out.str();
}
//------------------------------------------------------------------------------
std::string vframe_repr(TVFrame & r)
{
    std::stringstream out;
    out << "class 'TVFrame': { " << std::endl << vframe_str(r) << "}";
    return out.str();
}
//------------------------------------------------------------------------------
bp::tuple histogram(np::ndarray  &data, np::ndarray &histo, uint16_t orgThreshold, uint16_t topThreshold, float discardLevel)
{
    int scale = (1 << INP_PIX_W)/histo.shape(0);
    int shift = log2(scale);
    int count = data.shape(0)*data.shape(1);
    uint16_t *pixbuf  = reinterpret_cast<uint16_t *>( data.get_data() );
    uint32_t *histbuf = reinterpret_cast<uint32_t *>( histo.get_data() );
    
    for(int i = 0; i < count; ++i)
    {
        int pix = pixbuf[i] >> shift;
        histbuf[pix] += 1;
    }

    uint16_t min = 0;
    uint16_t max = 0;
    
    for(int i = 0; i < histo.shape(0); ++i) 
    {
        if(histbuf[i] >= orgThreshold)
        {
            min = i;
            break;
        }
    }
    
    uint16_t sum = 0;
    uint16_t upperLimit = histo.shape(0) - 1;
    
    for(int i = upperLimit; i; --i)
    {
        sum += histbuf[i];
        if(sum > discardLevel*count)
        {
            upperLimit = i;
            break;
        }
    }

    for(int i = upperLimit; i; --i) 
    {
        if(histbuf[i] >= topThreshold)
        {
            max = i;
            break;
        }
    }
    return bp::make_tuple(min*scale, max*scale, scale);
}
//------------------------------------------------------------------------------
void scale(np::ndarray &pixbuf, int sub, double k)
{
    int count = pixbuf.shape(0)*pixbuf.shape(1);
    uint16_t *buf  = reinterpret_cast<uint16_t *>( pixbuf.get_data() );
    
    for(int i = 0; i < count; ++i)
    {
        int val = buf[i];
        if(val - sub < 0)
        {
            buf[i] = 0;
        }
        else
        {
            val -= sub;
            uint32_t res = val*k;
            if(res > INP_PIX_MAXVAL)
                buf[i] = INP_PIX_MAXVAL;
            else 
                buf[i] = res;
        }
    }
}
//------------------------------------------------------------------------------
np::ndarray make_display_frame(np::ndarray &pixbuf)
{
    bp::tuple shape  = bp::make_tuple(FRAME_SIZE_Y, FRAME_SIZE_X);
    np::ndarray obuf = np::empty(shape, np::dtype::get_builtin<uint32_t>());
    
    size_t    count  = pixbuf.shape(0)*pixbuf.shape(1);
    uint16_t *idata  = reinterpret_cast<uint16_t *>( pixbuf.get_data() );
    uint32_t *odata  = reinterpret_cast<uint32_t *>( obuf.get_data() );

    for(size_t i = 0; i < count; ++i)
    {
        uint64_t val  = idata[i];
        odata[i] = val | (val << 10) | (val << 20);
    }
    
    return obuf;
}
//------------------------------------------------------------------------------
#include <unistd.h>

int get_frame(TVFrame &f)
{
    static uint16_t org = 0;

    uint16_t buf[FRAME_SIZE_Y][FRAME_SIZE_X];

    for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
    {
        for(size_t col = 0; col < FRAME_SIZE_X; ++col)
        {
            buf[row][col] = (org + row + col + 1) & OUT_PIX_MAXVAL;
            if(row == 100 && col == 100) buf[row][col] = 1023;
            if(row == 100 && col == 101) buf[row][col] = 1023/2;
        }
    }

    std::memcpy(f.pixbuf.get_data(),
                reinterpret_cast<uint8_t*>(buf),
                FRAME_SIZE_X*FRAME_SIZE_Y*sizeof(buf[0][0]));

    org += 10;

    return 1;
}
//------------------------------------------------------------------------------
void reg_pyobject(bp::object &pyobj, int idx)
{
    switch(idx)
    {
    case 0:
        inpframe_event = pyobj;
        break;
    case 1:
        vsthread_finish_event = pyobj;
        break;
    default:
        lg->error("invalid object index");
    }
}
//------------------------------------------------------------------------------
void iframe_event_set()
{
    GilLock gl;

    inpframe_event.attr("set")();
}
//------------------------------------------------------------------------------
void put_free_frame(TVFrame &f)
{
    free_frame_q.push(&f);
}
//------------------------------------------------------------------------------
TVFrame *get_iframe()
{
    TVFrame *f = incoming_frame_q.pop(std::chrono::milliseconds(4000));
    return f;
}
//------------------------------------------------------------------------------
//
//    Video Stream Thread stuff
//
void start_vstream_thread()
{
    lg->info("-------------------------------------------------------------\n\
                                                 Start Video Stream Thread\n");
    
    for(size_t i = 0; i < FRAME_POOL_SIZE; ++i)
    {
        TVFrame *pf = &frame_pool[i];
        pf->fnum = i;
        free_frame_q.push(pf);
        lg->info("free frame queue init: frame addr: {}", fmt::ptr(pf));
    }

    lg->info("free frame queue size:     {}", free_frame_q.size());
    lg->info("incoming frame queue size: {}", incoming_frame_q.size());
    vsthread_exit.store(false);

    {
        GilLock gl;

        vsthread_finish_event.attr("clear")();
    }

    vstream_thread = new std::thread(vstream_fun);
    lg->info("video stream processing thread started");
}
//------------------------------------------------------------------------------
void vsthread_finish_set()
{
    GilLock gl;

    vsthread_finish_event.attr("set")();
}
//------------------------------------------------------------------------------
void join_vstream_thread()
{
    vsthread_exit.store(true);
    vstream_thread->join();
    free_frame_q.clear();
    incoming_frame_q.clear();
    lg->info("free frame queue size:     {}", free_frame_q.size());
    lg->info("incoming frame queue size: {}", incoming_frame_q.size());
    vsthread_finish_set();
    lg->info("video stream processing thread finished");
    lg->info("-------------------------------------------------------------\n");
}
//------------------------------------------------------------------------------
void finish_vstream_thread()
{
    auto vsthread_finalize = new std::thread(join_vstream_thread);
    vsthread_finalize->detach();
    lg->info("-------------------------------------------------------------\n\
                                                 Stop Video Stream Thread\n");
    lg->info("video stream processing thread finish pending...");
}
//------------------------------------------------------------------------------
//
//    Boost.Python Module
//
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;

    scope().attr("FRAME_SIZE_X") = FRAME_SIZE_X;
    scope().attr("FRAME_SIZE_Y") = FRAME_SIZE_Y;
    scope().attr("OUT_PIX_W")    = OUT_PIX_W;

    //--------------------------------------------------------------------------
    //
    //    Video frame wrap definitions
    //
    {
        scope vframe_scope =
        class_<TVFrame>("TVFrame", init<>())
            .add_property("fnum",   &TVFrame::fnum)
            .add_property("tstamp", &TVFrame::tstamp)
            .add_property("size_x", &TVFrame::size_x)
            .add_property("size_y", &TVFrame::size_y)
            .add_property("pixbuf", make_getter(&TVFrame::pixbuf))
            .def("copy",   &TVFrame::copy)
            .def("rshift", &TVFrame::rshift)
            .def("divide", &TVFrame::divide)
            .def("__str__",  vframe_str)
            .def("__repr__", vframe_repr)
        ;
    }
    //--------------------------------------------------------------------------
    //
    //    Common exposed functions
    //
    def("init_numpy",            init_numpy);
    def("get_frame",             get_frame);
    def("histogram",             histogram);
    def("scale",                 scale);
    def("make_display_frame",    make_display_frame);

    def("create_frame_pool",     create_frame_pool);
    def("delete_frame_pool",     delete_frame_pool);
    def("start_vstream_thread",  start_vstream_thread);
    def("finish_vstream_thread", finish_vstream_thread);
    def("reg_pyobject",          reg_pyobject);
    def("put_free_frame",        put_free_frame);
    def("get_iframe",            get_iframe, return_value_policy<reference_existing_object>());
}
//------------------------------------------------------------------------------

