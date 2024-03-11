//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Timing measure stuff
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

#ifndef TIME_H
#define TIME_H

#ifdef _MSC_VER
// Windows
#include <Windows.h>
#else
// Linux
#include <time.h>
#endif
/// return a timestamp with sub-second precision
/** QueryPerformanceCounter and clock_gettime have an undefined starting point (null/zero)
    and can wrap around, i.e. be nulled again. **/
double seconds()
{
#ifdef _MSC_VER
  static LARGE_INTEGER frequency;
  if (frequency.QuadPart == 0)
    ::QueryPerformanceFrequency(&frequency);
  LARGE_INTEGER now;
  ::QueryPerformanceCounter(&now);
  return now.QuadPart / double(frequency.QuadPart);
#else
  struct timespec now;
  clock_gettime(CLOCK_MONOTONIC, &now);
  return now.tv_sec + now.tv_nsec / 1000000000.0;
#endif
}

#endif // TIME_H
//-------------------------------------------------------------------------------
