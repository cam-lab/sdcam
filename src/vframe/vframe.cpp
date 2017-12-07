
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#pragma GCC diagnostic pop


#include <iostream>
#include <stdint.h>

#include "timing.h"
#include <unistd.h>

#include <ip_qpipe_def.h>

#include <array_ref.h>
#include <array_indexing_suite.h>

using namespace IP_QPIPE_LIB;

namespace bp = boost::python;
namespace np = boost::python::numpy;


const uint16_t FRAME_SIZE_X = 8; // 1280;
const uint16_t FRAME_SIZE_Y = 4; // 960;

//uint16_t frame[FRAME_SIZE_Y*FRAME_SIZE_X];

//------------------------------------------------------------------------------
void init_numpy()
{
    np::initialize();
}
//------------------------------------------------------------------------------
struct A
{
    int x;
    int y;
};
struct B
{
    B() : Arr(np::empty(bp::make_tuple(4), np::dtype::get_builtin<uint32_t>())) { }
    bp::object ndarr() { return Arr; }
    
    int c;
    A   a;
    np::ndarray Arr;
};
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
    A           a;
    np::ndarray pixbuf;
};

void f(TVFrame *f)
{
    std::cout << "pixbuf: " << bp::extract<const char *>(bp::str(f->pixbuf)) << std::endl;
    std::cout << "a.x: " << f->a.x << ", a.y: " << f->a.y << std::endl;
}
uint32_t g(TVFrame &f)
{
    f.a.x = 123;
    f.a.y = 987;
    return 4;
}
//------------------------------------------------------------------------------
void ff()
{
    std::cout << "slonick!" << std::endl;
}
//------------------------------------------------------------------------------
typedef boost::function<void () > fptr;

void pff( fptr fp )
{
    fp();
}

void pfff(bp::object& func)
{
    func();
}

std::string pipe_info_str(TPipeInfo & r, std::string offset)
{
    std::stringstream out;
    out << offset << "chunkSize: "   << r.chunkSize  << std::endl
        << offset << "chunkNum:  "   << r.chunkNum   << std::endl
        << offset << "txReady:   "   << r.txReady    << std::endl
        << offset << "rxReady:   [ " << r.rxReady[0] << ", "
                                     << r.rxReady[1] <<  ", "
                                     << r.rxReady[2] <<  ", "
                                     << r.rxReady[3] << " ]" << std::endl;
    return out.str();
}

std::string pipe_info_repr(TPipeInfo & r)
{   
    std::stringstream out;
    out << "PipeInfo: { " << std::endl << pipe_info_str(r, "  ") << "}";
    return out.str();
}

std::string pipe_rx_params_str(TPipeRxParams & r)
{
    std::stringstream out;
    out << "  key:       " << r.pipeKey   << std::endl
        << "  isCreated: " << r.isCreated << std::endl
        << "  id:        " << r.pipeId    << std::endl
        << "  info:      " << std::endl
        << pipe_info_str(r.pipeInfo, "    ");

    return out.str();
}

std::string pipe_rx_params_repr(TPipeRxParams & r)
{
    std::stringstream out;
    out << "PipeRxParams: { " << std::endl << pipe_rx_params_str(r) << "}";
    return out.str();
}


void pipe_rx_params(TPipeRxParams *p)
{
    std::cout << "key: " << p->pipeKey << ", isCreated: " << p->isCreated << ", id: " << p->pipeId << std::endl;
    std::cout << "chunkSize: "  << p->pipeInfo.chunkSize
       << ", chumkNum: " << p->pipeInfo.chunkNum
       << ", txReady: "  << p->pipeInfo.txReady
       << std::endl;
    
    p->pipeKey++;
    p->isCreated += 2;
    p->pipeId += 4;
    
    for(int i = 0; i < 4; ++i)
    {
        std::cout << "rxReady[" << i << "] :" << p->pipeInfo.rxReady[i] << std::endl;
        p->pipeInfo.rxReady[i]++;
    }
}
//------------------------------------------------------------------------------
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;

    {
        scope vframe_scope =
        class_<TVFrame>("TVFrame", init<>())
            .add_property("size_x", &TVFrame::size_x)
            .add_property("size_y", &TVFrame::size_y)
            .add_property("a", &TVFrame::a)
            .add_property("pixbuf", make_getter(&TVFrame::pixbuf))
        ;
        
        class_<A>("A")
            .add_property("x", make_getter(&A::x), make_setter(&A::x))
            .add_property("y", make_getter(&A::y), make_setter(&A::y))
        ;
    }
    
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
    
    
    def("init_numpy", &init_numpy);
    def("print_frame", f);
    def("change_a", g);
    def("pipe_rx_params", &pipe_rx_params);
    
    def("ff", ff);
    def("pff", pff);
    def("pfff", pfff);
    
    class_<B>("B", init<>())
        .add_property("c", &B::c)
        .def_readwrite("a", &B::a)
        .def("Arr", &B::ndarr)
    ;

}
//------------------------------------------------------------------------------

