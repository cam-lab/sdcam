//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Thread-safe Queue
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

#ifndef TSQUEUE_H
#define TSQUEUE_H

#include <stdint.h>
#include <iostream>
#include <queue>
#include <mutex>
#include <condition_variable>

#include "utils.h"

//------------------------------------------------------------------------------
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
//------------------------------------------------------------------------------

template<typename T>
class tsqueue
{
public:
    void push(T item)
    {
        std::unique_lock<std::mutex> lk(mtx);

        queue.push(item);
        flag.notify_one();
    }

    T pop(const std::chrono::milliseconds timeout)
    {
        std::unique_lock<std::mutex> lk(mtx);

        if( flag.wait_for(lk, timeout, [this]() { return !queue.empty(); }) )
        {
            T item = queue.front();
            queue.pop();
            return item;
        }
        
        print("tsqueue::pop, timeout or spurious wakeup");
        return nullptr;   // timeout expired

    }
    
    size_t size()
    {
        std::unique_lock<std::mutex> lk(mtx);

        return queue.size();
    }
    
private:
    std::queue<T>           queue;
    std::mutex              mtx;
    std::condition_variable flag;
};

//------------------------------------------------------------------------------
#if defined( __GNUG__ )

#pragma GCC diagnostic pop

#elif defined(_MSC_VER)

#pragma warning( pop )  

#else

#error("E: unsupported compiler. Only GCC and MSVC are supported for now")

#endif //  __GNUC__

#endif // TSQUEUE_H
//------------------------------------------------------------------------------

