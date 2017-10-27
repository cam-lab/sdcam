
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <boost/python.hpp>
#include <boost/python/numpy.hpp>

#include <iostream>
#include <stdint.h>

//#include <chrono>
//#include <thread>

#include "timing.h"
#include <unistd.h>

namespace bp = boost::python;
namespace np = boost::python::numpy;

double sqroot(double a) {
  return std::sqrt(a);
}


//std::vector<double> list_of_nums() {
  //return std::vector<double>{1,2,3,4,5};
//}

const uint16_t FRAME_SIZE_X = 1280;
const uint16_t FRAME_SIZE_Y = 960;

uint16_t frame[FRAME_SIZE_Y*FRAME_SIZE_X];

uint16_t arr[] = {1,2,3,4,5};

//------------------------------------------------------------------------------
void init_numpy()
{
    np::initialize();
}
//------------------------------------------------------------------------------
void gen_frame()
{
    for(int i = 0; i < sizeof(frame)/sizeof(frame[0]); ++i)
    {
        frame[i] += i;
    }
}
//------------------------------------------------------------------------------
class TFrame {
public:
    TFrame() 
        : Data(np::empty(bp::make_tuple(1), np::dtype::get_builtin<uint16_t>() ) ) 
    {
        //auto idx = 0;  //only one element
        //*(reinterpret_cast<uint16_t *>(Data.get_data())+idx) = d[0];
    }


    void load(uint16_t *d, size_t count)
    {
        double t1 = seconds();
        Data = np::from_data(d, np::dtype::get_builtin<uint16_t>(),
                             bp::make_tuple(count),
                             bp::make_tuple(sizeof(uint16_t)),
                             bp::object()).reshape(bp::make_tuple(FRAME_SIZE_X, FRAME_SIZE_Y));
        double t2 = seconds();
        std::cout << "c++ create frame (from_data and reshape: " << t2 - t1 << std::endl;
    }
        
    bp::object data() 
    {
        return Data;
    }
    
    double read()
    {
        //std::this_thread::sleep_for(std::chrono::milliseconds(40));
        usleep(40000);

        double t1 = seconds();
        gen_frame();
        double t2 = seconds();
        load(frame, sizeof(frame)/sizeof(uint16_t));
        double t3 = seconds();
        std::cout << "gen frame: " << t2 - t1 << " load: " << t3 - t2 << std::endl;
        //std::cout << "frame data: " << bp::extract<char const *>(bp::str(Data)) << std::endl;
        return seconds();
    }
    
private:
    np::ndarray Data;
};
//------------------------------------------------------------------------------
np::ndarray &get_frame()
{
    static np::ndarray py_array = np::from_data(arr, np::dtype::get_builtin<int>(),
                                     bp::make_tuple(5),
                                     bp::make_tuple(sizeof(int)),
                                     bp::object());
    
    return py_array;
}
//------------------------------------------------------------------------------
void init_frame()
{
//  for(int row = 0; row < FRAME_SIZE_Y; ++row)
//  {
//      for(int col = 0; col < FRAME_SIZE_X; ++col)
//      {
//          frame[row][col] = row + col;
//      }
//  }

    for(int i = 0; i < sizeof(frame)/sizeof(frame[0]); ++i)
    {
        frame[i] = i;
    }


    std::cout << "C++ array:" << std::endl;
    for (int j = 0; j < 5; ++j)
    {
        std::cout << arr[j] << ' ';
    }
    
    np::ndarray &py_array = get_frame(); 
    std::cout << std::endl
              << "Python ndarray: " << bp::extract<char const *>(bp::str(py_array)) << std::endl;

}
//------------------------------------------------------------------------------
BOOST_PYTHON_MODULE(vframe)
{
    using namespace boost::python;
    //boost::python::numeric::array::set_module_and_type("numpy", "ndarray");
    //import_array();

    def("sqroot",     &sqroot);
    def("init_numpy", &init_numpy);
    def("init_frame", &init_frame);
    
 
    //class_<TFrame>("Frame", init<uint16_t *, size_t>())
    class_<TFrame>("Frame")
        .def("data", &TFrame::data)
        .def("read", &TFrame::read)
    ;
    

    //def("get_frame",  &get_frame);
    // def("list_of_nums", &list_of_nums);

    //class_<std::vector<double> >("MyVector")
        //.def(vector_indexing_suite<std::vector<double> >())
        //;
}
//------------------------------------------------------------------------------

