//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Console Progress Bar
//
//    Based on example from:
//
//        https://codereview.stackexchange.com/questions/186535/progress-bar-in-c
//
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

#ifndef PROGRESS_BAR_H
#define PROGRESS_BAR_H

#include <cmath>
#include <iomanip>
#include <ostream>
#include <string>

//-------------------------------------------------------------------------------
class ProgressBar
{
    static const auto overhead = sizeof " [100%]";

    std::ostream       &os;
    const std::size_t  bar_width;
    std::string        message;
    const std::string  full_bar;

 public:
    ProgressBar(std::ostream& os, std::size_t line_width,
                 std::string message_, const char symbol = '.')
        : os{os}
        , bar_width{line_width - overhead}
        , message{std::move(message_)}
        , full_bar{std::string(bar_width, symbol) + std::string(bar_width, ' ')}
    {
        if (message.size()+1 >= bar_width || message.find('\n') != message.npos) {
            os << message << '\n';
            message.clear();
        } else {
            message += ' ';
        }
        write(0.0);
    }

    // not copyable
    ProgressBar(const ProgressBar &)            = delete;
    ProgressBar& operator=(const ProgressBar &) = delete;

    ~ProgressBar()
    {
        write(1.0);
        os << '\n';
    }

    void write(double fraction);
};

void ProgressBar::write(double fraction)
{
    // clamp fraction to valid range [0,1]
    if (fraction < 0)
        fraction = 0;
    else if (fraction > 1)
        fraction = 1;

    auto width = bar_width - message.size();
    auto offset = bar_width - static_cast<unsigned>(width * fraction);

    os << '\r' << message;
    os.write(full_bar.data() + offset, width);
    os << " [" << std::setw(3) << static_cast<int>(100*fraction) << "%] " << std::flush;
}

#endif // PROGRESS_BAR_H
//-------------------------------------------------------------------------------
