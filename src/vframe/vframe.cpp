

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


#include <stdint.h>
#include <iostream>
#include <cmath>

#include "timing.h"
#include "vframe.h"

#include <array_ref.h>
#include <array_indexing_suite.h>

//------------------------------------------------------------------------------
void init_numpy()
{
    np::initialize();
}
//------------------------------------------------------------------------------
TVFrame::TVFrame()
    : host_fnum      ( 0 )
    , host_fpixsize  ( 2 )             // bytes
    , host_fsize_x   ( FRAME_SIZE_X )  
    , host_fsize_y   ( FRAME_SIZE_Y )  
    
    , meta_buf_size  ( 0 )
    , meta_elem_size ( 0 )
    , meta_info_size ( 0 )

    , fnum           ( 0 )
    , tstamp         ( 0 )
    , size_x         ( 0 )
    , size_y         ( 0 )
    , pixwidth       ( 0 )
                     
    , det_cr         ( 0 )
    , det_iexp       ( 0 )
    , det_fexp       ( 0 )
    , det_pga_code   ( 0 )
                     
    , npulses        ( 0 )
    , pinch          ( 0 )
    , depth          ( 0 )
    , trim           ( 0 )

    , pwidth         ( 0 )
     
    , pixbuf(np::empty(bp::make_tuple(FRAME_SIZE_Y, FRAME_SIZE_X), np::dtype::get_builtin<uint16_t>()))
    , rawbuf(np::empty(bp::make_tuple(RAWBUF_SIZE/sizeof(uint32_t)), np::dtype::get_builtin<uint32_t>()))
{
}
//------------------------------------------------------------------------------
bool TVFrame::fill(uint8_t *src, uint32_t len)
{
    uint32_t *buf = reinterpret_cast<uint32_t *>(src);
    
    //--------------------------------------------------------------------------
    //
    //   Host data
    //
    if(buf[0] != 0) return false;

    host_fnum = buf[6];

    if(buf[7] != host_fpixsize) return false;
    if(buf[8] != host_fsize_y)  return false;
    if(buf[9] != host_fsize_x)  return false;
    
    //--------------------------------------------------------------------------
    //
    //   Meta info
    //
    meta_buf_size  = buf[META_INFO_HEADER_OFFSET];
    meta_elem_size = buf[META_INFO_HEADER_OFFSET+1];
    meta_info_size = buf[META_INFO_HEADER_OFFSET+2];
    
    uint16_t *minfo = reinterpret_cast<uint16_t *>(buf + META_INFO_DATA_OFFSET);
    
    fnum          = retreive_fnum(minfo);
    tstamp        = retreive_tstamp(minfo + TSTAMP_OFFSET); 
    size_x        = minfo[SIZE_X_OFFSET];
    size_y        = minfo[SIZE_Y_OFFSET];
    pixwidth      = minfo[PIXWIDTH_OFFSET];
                  
    det_cr        = minfo[DET_CR_OFFSET];
    det_iexp      = minfo[DET_IEXP_OFFSET]; 
    det_fexp      = minfo[DET_FEXP_OFFSET]; 
    det_pga_code  = minfo[DET_PGA_CODE_OFFSET]; 

    npulses       = minfo[NPULSES_OFFSET]; 
    pinch         = minfo[PINCH_OFFSET]; 
    depth         = minfo[DEPTH_OFFSET]; 
    trim          = minfo[TRIM_OFFSET];
    
    pwidth        = minfo[PWIDTH_OFFSET];
    
    //--------------------------------------------------------------------------
    //
    //   Check length
    //
    if(META_INFO_DATA_OFFSET*sizeof(uint32_t) + meta_buf_size + host_fsize_x*host_fsize_y*host_fpixsize != len)
    {
        std::cout << "E: incorrect chunk data length" << std::endl;
        return false;
    }

    //--------------------------------------------------------------------------
    //
    //   Pixel array
    //
    std::memcpy(pixbuf.get_data(), 
                src + META_INFO_DATA_OFFSET*sizeof(uint32_t) + meta_buf_size, 
                host_fsize_x*host_fsize_y*host_fpixsize);
    
    return true;
}
//------------------------------------------------------------------------------
uint32_t TVFrame::retreive_fnum(uint16_t *p)
{
    return (  p[0] & 0xff)        +
           ( (p[1] & 0xff) << 8)  +
           ( (p[2] & 0xff) << 16) +
           ( (p[3] & 0xff) << 24);
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
uint64_t TVFrame::retreive_tstamp(uint16_t *p)
{
    uint32_t l = (  p[0] & 0xff)        +
                 ( (p[1] & 0xff) << 8)  +
                 ( (p[2] & 0xff) << 16) +
                 ( (p[3] & 0xff) << 24);
    
    uint64_t h = (  p[4] & 0xff)        +
                 ( (p[5] & 0xff) << 8)  +
                 ( (p[6] & 0xff) << 16) +
                 ( (p[7] & 0xff) << 24);
        
    return l + (h << 32);
}
//------------------------------------------------------------------------------
std::string vframe_str(TVFrame & r)
{
    std::stringstream out;
    out << "    host_fnum     : " << r.host_fnum     << std::endl
        << "    fnum          : " << r.fnum          << std::endl
        << "    size_x        : " << r.size_x        << std::endl
        << "    size_y        : " << r.size_y        << std::endl
        << "    pixwidth      : " << r.pixwidth      << std::endl
        << "    det_cr        : " << r.det_cr        << std::endl
        << "    det_iexp      : " << r.det_iexp      << std::endl
        << "    det_fexp      : " << r.det_fexp      << std::endl
        << "    det_pga_code  : " << r.det_pga_code  << std::endl
        << "    npulses       : " << r.npulses       << std::endl
        << "    pinch         : " << r.pinch         << std::endl
        << "    depth         : " << r.depth         << std::endl
        << "    trim          : " << r.trim          << std::endl
        << "    pwidth        : " << r.pwidth        << std::endl; 

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
    int scale = (1 << VIDEO_DATA_WIDTH)/histo.shape(0); 
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
            if(res > VIDEO_DATA_MAX) 
                buf[i] = VIDEO_DATA_MAX;
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
    uint32_t *odata  = reinterpret_cast<uint32_t  *>( obuf.get_data() );

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
            buf[row][col] = (row + col + 1) & VIDEO_OUT_DATA_MAX;
            if(row == 100 && col == 100) buf[row][col] = 1023;
            if(row == 100 && col == 101) buf[row][col] = 1023/2;
        }
    }

    std::memcpy(f.pixbuf.get_data(),
                reinterpret_cast<uint8_t*>(buf),
                FRAME_SIZE_X*FRAME_SIZE_Y*sizeof(buf[0][0]));

    //org += 20;

    return 1;
}

//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;

    scope().attr("FRAME_SIZE_X")         = FRAME_SIZE_X;
    scope().attr("FRAME_SIZE_Y")         = FRAME_SIZE_Y;
    scope().attr("VIDEO_OUT_DATA_WIDTH") = VIDEO_OUT_DATA_WIDTH;

    //--------------------------------------------------------------------------
    //
    //    Video frame wrap definitions
    //
    {
        scope vframe_scope =
        class_<TVFrame>("TVFrame", init<>())
            .add_property("host_fnum", &TVFrame::host_fnum)
            .add_property("fnum",   &TVFrame::fnum)
            .add_property("tstamp", &TVFrame::tstamp)
            .add_property("size_x", &TVFrame::size_x)
            .add_property("size_y", &TVFrame::size_y)
            .add_property("iexp",   &TVFrame::det_iexp)
            .add_property("fexp",   &TVFrame::det_fexp)
            .add_property("pixbuf", make_getter(&TVFrame::pixbuf))
            .add_property("rawbuf", make_getter(&TVFrame::rawbuf))
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
    def("init_numpy",         init_numpy);
    def("get_frame",          get_frame);
    def("histogram",          histogram);
    def("scale",              scale);
    def("make_display_frame", make_display_frame);
}
//------------------------------------------------------------------------------

