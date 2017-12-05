
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>

#include <iostream>
#include <stdint.h>

#include "timing.h"
#include <unistd.h>

#include <ip_qpipe_def.h>

//using namespace IP_QPIPE_LIB;

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
       , pixbuf(np::empty(bp::make_tuple(FRAME_SIZE_X*FRAME_SIZE_Y), np::dtype::get_builtin<uint16_t>()))
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
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;

    {
        scope outer =
        class_<TVFrame>("TVFrame", init<>())
            .add_property("size_x", &TVFrame::size_x)
            .add_property("size_y", &TVFrame::size_y)
            //.add_property("a", make_getter(&TVFrame::a), make_setter(&TVFrame::a))
            //.add_property("a", make_getter(&TVFrame::a))
            .add_property("a", &TVFrame::a)
            .add_property("pixbuf", make_getter(&TVFrame::pixbuf))
            .def("pbuf", &TVFrame::pbuf)
        ;
        
        class_<A>("A")
            .add_property("x", make_getter(&A::x), make_setter(&A::x))
            .add_property("y", make_getter(&A::y), make_setter(&A::y))
        ;
    }
    
    
    def("print_frame", f);
    def("change_a", g);
    
    class_<B>("B", init<>())
        .add_property("c", &B::c)
        .def_readwrite("a", &B::a)
        .def("Arr", &B::ndarr)
    ;
    def("init_numpy", &init_numpy);
    
//  {
//      scope in_TPipeRxParams =
//      class_<TPipeRxParams>("PipeRxParams")
//          .add_property("Key",       make_getter(&TPipeRxParams::Key),   make_setter(&TPipeRxParams::Key))
//          .add_property("isCreated", make_getter(&TPipeRxParams::isCreated), make_setter(&TPipeRxParams::isCreated))
//          .add_property("Id",        make_getter(&TPipeRxParams::Id   ), make_setter(&TPipeRxParams::Id   ))
//      ;
//
//  }
    
    

}
//------------------------------------------------------------------------------

