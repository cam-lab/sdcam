

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