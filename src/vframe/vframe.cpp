
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#pragma GCC diagnostic pop


#include <stdint.h>
#include <iostream>

#include "timing.h"
#include <unistd.h>

#include "qpipe_cfg.h"

#include <array_ref.h>
#include <array_indexing_suite.h>

namespace bp = boost::python;
namespace np = boost::python::numpy;


const uint16_t FRAME_SIZE_X = 8; // 1280;
const uint16_t FRAME_SIZE_Y = 4; // 960;

//------------------------------------------------------------------------------
void init_numpy()
{
    np::initialize();
}
//------------------------------------------------------------------------------
struct TVFrame
{
    TVFrame()
       : size_x(FRAME_SIZE_X)
       , size_y(FRAME_SIZE_Y)
       , pixbuf(np::empty(bp::make_tuple(FRAME_SIZE_Y, FRAME_SIZE_X), np::dtype::get_builtin<uint16_t>()))
    {
    }
    
    bp::object pbuf() { return pixbuf; }
    
    uint32_t    size_x;
    uint32_t    size_y;
    np::ndarray pixbuf;
};
//------------------------------------------------------------------------------
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;

    //--------------------------------------------------------------------------
    //
    //    Video frame wrap definitions
    //
    {
        scope vframe_scope =
        class_<TVFrame>("TVFrame", init<>())
            .add_property("size_x", &TVFrame::size_x)
            .add_property("size_y", &TVFrame::size_y)
            .add_property("pixbuf", make_getter(&TVFrame::pixbuf))
        ;
    }
    
    //--------------------------------------------------------------------------
    //
    //    qpipe parameters wrap definitions
    //
    {
        scope qpipe_rx_params_scope = 
        class_<TPipeRxParams>("TPipeRxParams")
            .add_property("key",       make_getter(&TPipeRxParams::pipeKey  ), make_setter(&TPipeRxParams::pipeKey  ))
            .add_property("isCreated", make_getter(&TPipeRxParams::isCreated), make_setter(&TPipeRxParams::isCreated))
            .add_property("id",        make_getter(&TPipeRxParams::pipeId   ), make_setter(&TPipeRxParams::pipeId   ))
            .add_property("info",      make_getter(&TPipeRxParams::pipeInfo ), make_setter(&TPipeRxParams::pipeInfo ))
            .def("__str__",  pipe_rx_params_str)
            .def("__repr__", pipe_rx_params_repr)
        ;

        class_< array_ref<uint32_t> >("uint32_t_array")
            .def( array_indexing_suite< array_ref<uint32_t> >() )
        ;
        
        class_<TPipeInfo>("TPipeInfo")
            .add_property("chunkSize", make_getter(&TPipeInfo::chunkSize), make_setter(&TPipeInfo::chunkSize))
            .add_property("chunkNum",  make_getter(&TPipeInfo::chunkNum),  make_setter(&TPipeInfo::chunkNum))
            .add_property("txReady",   make_getter(&TPipeInfo::txReady),   make_setter(&TPipeInfo::txReady))
            .add_property("rxReady",   
                          // getter that returns an array_ref view into the array
                          //static_cast< array_ref<uint32_t>(*)(TPipeInfo *) >([](TPipeInfo *obj)
                          (+[](TPipeInfo *obj)
                          {
                              return array_ref<uint32_t>(obj->rxReady);
                          }),
                          "Array of 'rxReady'")
            .def("__str__",  pipe_info_str)
            .def("__repr__", pipe_info_repr)
        ;
    }
    
    //--------------------------------------------------------------------------
    //
    //    Common exposed functions
    //
    def("init_numpy",     init_numpy);
    def("qpipe_cfg",      qpipe_cfg);
    def("pipe_rx_params", pipe_rx_params);
}
//------------------------------------------------------------------------------

