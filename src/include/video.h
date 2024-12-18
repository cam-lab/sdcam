//-------------------------------------------------------------------------------
//
//    Project: Software-Defined Camera
//
//    Purpose: Processing video
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

//------------------------------------------------------------------------------
#include "vframe.h"
#include "socket.h"

//const char     *SOCKET_IP = "127.0.0.1";
const char     *SOCKET_IP = "192.168.10.1";
const uint16_t  SRC_PORT  = 50001;
const size_t    PKT_SIZE  = 2048;

class FrameReceiver
{
    using SockBuf    = std::array<uint16_t, PKT_SIZE/sizeof(uint16_t)>;
    using FieldBuf   = std::array<uint16_t, 8>;
    
    enum State
    {
        stateFSYNC,
        stateLSYNC,
        stateFRAME_NUM,
        stateTIME_STAMP,
        stateLINE_NUM,
        stateFRAME_WIDTH,
        stateFRAME_HEIGHT,
        statePIXEL_WIDTH,
        stateDATA
    };

public:
    FrameReceiver(FrameQueue &fq,
                  FrameQueue &iq,
                  Socket     &s,
                  Logger      logger)
       : sock             ( s          )
       , pkt_idx          ( 0          )
       , pkt_count        ( 0          )
       , state            ( stateFSYNC )
       , free_frame_q     ( fq         )
       , incoming_frame_q ( iq         )
       , frame            ( nullptr    )
       , lg               ( logger     )
    {

    }
    
    inline void recv();

private:
    inline void fsync            (uint16_t item);
    inline void lsync            (uint16_t item);
    inline void frame_num        (uint16_t item);
    inline void timestamp        (uint16_t item);
    inline void line_num         (uint16_t item);
    inline void frame_width      (uint16_t item);
    inline void frame_height     (uint16_t item);
    inline void pixel_width      (uint16_t item);
    inline bool data             (uint16_t item);

    inline void check_test_frame ();

private:
    Socket      &sock;
    size_t       pkt_idx;
    size_t       pkt_count;
    State        state;
    FrameQueue  &free_frame_q;
    FrameQueue  &incoming_frame_q;
    Vframe      *frame;
    Logger       lg;

    FieldBuf     field_buf;
    size_t       field_idx;
    SockBuf      pkt;
    size_t       row;
    size_t       col;

    size_t       size_x;
    size_t       size_y;
    size_t       row_cnt;
};
//------------------------------------------------------------------------------
void FrameReceiver::recv()
{
    while(1)
    {
        int count = 0;
        if( !pkt_count )
        {
            //lg->info("before sock.read, pkt_count: {}", pkt_count);
            count = sock.read(reinterpret_cast<uint8_t *>(pkt.data()), PKT_SIZE);
        }
        
        if(count >= 0)
        {
            pkt_count = count/sizeof(uint16_t);
            //lg->info("pkt count: {}", pkt_count);
            for(auto i = pkt_idx; i < pkt_count; ++i)
            {
                //lg->info("{:03} : {:04x}", i, pkt[i]);
                switch(state)
                {
                case stateFSYNC        : fsync        ( pkt[i] ); break;
                case stateFRAME_NUM    : frame_num    ( pkt[i] ); break;
                case stateTIME_STAMP   : timestamp    ( pkt[i] ); break;
                case stateFRAME_WIDTH  : frame_width  ( pkt[i] ); break;
                case stateFRAME_HEIGHT : frame_height ( pkt[i] ); break;
                case statePIXEL_WIDTH  : pixel_width  ( pkt[i] ); break;
                case stateLSYNC        : lsync        ( pkt[i] ); break;
                case stateLINE_NUM     : line_num     ( pkt[i] ); break;
                case stateDATA         :
                    {
                        if(data(pkt[i]))
                        {
                            pkt_idx = ++i;
                            return;          // frame complete, pass control to thread function
                        }
                    }
                }
            }
            pkt_count = 0;  // make ready to get data from socket
            pkt_idx   = 0;
        }
        else
        {
            //lg->info("socket timeout");
            return;  // timeout: there are no data from socket, pass control to thread function
        }
    }
}
//------------------------------------------------------------------------------
void FrameReceiver::fsync(uint16_t item)
{
    if(!frame)
    {
        frame = free_frame_q.pop(std::chrono::milliseconds(1000));
        //lg->info("pop frame pointer for new frame");
    }

    if( !frame )
    {
        return;
    }

    if(item & CFT_MASK)
    {
        return;
    }
    else if(item & VST_MASK)
    {
        //lg->info("VST incoming");
        if((item & FTT_MASK) == 0)                    // frame MDB
        {
            //lg->info("Frame MDB detected");
            if( (item & MDBS_MASK) == FRAME_MDB_SIZE )
            {

                field_idx = 0;
                row       = 0;
                col       = 0;
                row_cnt   = 0;
                state     = stateFRAME_NUM;
            }
            else
            {
                lg->error("invalid FMDBS: {}. Must be {}", item & MDBS_MASK, FRAME_MDB_SIZE);
            }
        }
        else
        {
            lg->error("invalid VST type: expected frame VST, got: {:x}", item);
        }
    }
}
//------------------------------------------------------------------------------
void FrameReceiver::lsync(uint16_t item)
{
    if(item & CFT_MASK)
    {
        return;
    }
    else if(item & VST_MASK)
    {
        //lg->info("VST incoming");
        if( (item & FTT_MASK) )                    // line MDB
        {
            //lg->info("Line MDB detected");
            if( (item & MDBS_MASK) == 1 )
            {
                col   = 0;
                state = stateLINE_NUM;
            }
            else
            {
                lg->error("<line> invalid LMDBS: {}. Must be {}", item & MDBS_MASK, 1);
            }
        }
        else
        {
            lg->error ("invalid VST type: expected line VST, got: {:x}", item);
            lg->warn  ("drop current frame: {}, begin sync new frame", frame->fnum);
            state = stateFSYNC;
        }
    }
}
//------------------------------------------------------------------------------
void FrameReceiver::frame_num(uint16_t item)
{
    field_buf[field_idx++] = item;
    if(field_idx == FNUM_SIZE)
    {
        frame->retreive_fnum(field_buf.data());
        field_idx = 0;
        state     = stateTIME_STAMP;
        //lg->info("Frame Number: {:x}", frame->fnum);
    }
}
//------------------------------------------------------------------------------
void FrameReceiver::timestamp(uint16_t item)
{
    field_buf[field_idx++] = item;
    if(field_idx == TSTUMP_SIZE)
    {
        frame->retreive_tstamp(field_buf.data());
        state = stateFRAME_WIDTH;
        //lg->info("Time Stamp: {:x}", frame->tstamp);
    }
}
//------------------------------------------------------------------------------
void FrameReceiver::frame_width(uint16_t item)
{
    frame->size_x = item;
    size_x        = item;
    state         = stateFRAME_HEIGHT;
    //lg->info("Frame Width: {}", frame->size_x);
}
//------------------------------------------------------------------------------
void FrameReceiver::frame_height(uint16_t item)
{
    frame->size_y = item;
    size_y        = item;
    state         = statePIXEL_WIDTH;
    //lg->info("Frame Height: {}", frame->size_y);
}
//------------------------------------------------------------------------------
void FrameReceiver::pixel_width(uint16_t item)
{
    frame->pixwidth = item;
    state           = stateLSYNC;
    //lg->info("Pixel Width: {}", frame->pixwidth);
}
//------------------------------------------------------------------------------
void FrameReceiver::line_num(uint16_t item)
{
    row   = item & LNUM_MASK;
    col   = 0;
    state = stateDATA;
    //lg->info("<line> Line Number: {}", row);
}
//------------------------------------------------------------------------------
bool FrameReceiver::data(uint16_t item)
{
    //lg->info("item: {:x}", item);
    //frame->pixbuf[row][col++] = item & INP_PIX_MAXVAL;
    uint16_t *ptr = reinterpret_cast<uint16_t *>(frame->pixbuf.get_data());
    ptr[row*size_x + col++] =  item & INP_PIX_MAXVAL;

    static uint32_t prev_fnum;

    if(col == size_x)
    {
        //lg->info("<line> line {} complete", row);
        if(++row_cnt == size_y)
        {
            if(prev_fnum+1 != frame->fnum)
            {
                lg->warn("frame lost! prev_fnum: {}, current fnum {}", prev_fnum, frame->fnum);

            }

            prev_fnum = frame->fnum;

            check_test_frame();

            //lg->info("frame {:x} complete", frame->fnum);
            incoming_frame_q.push(frame);
            iframe_event_set();
            frame = nullptr;
            state = stateFSYNC;
            return true;
        }
        state = stateLSYNC;
    }
    
    return false;
}
//------------------------------------------------------------------------------
void FrameReceiver::check_test_frame()
{
    uint16_t (&pixbuf)[FRAME_SIZE_Y][FRAME_SIZE_X] = *reinterpret_cast<uint16_t (*)[FRAME_SIZE_Y][FRAME_SIZE_X]>(frame->pixbuf.get_data());
    uint16_t org = pixbuf[0][0];
    
    for(size_t row = 0; row < FRAME_SIZE_Y; ++row)
    {
        for(size_t col = 0; col < FRAME_SIZE_X; ++col)
        {
            uint16_t val = (org + row + col) & OUT_PIX_MAXVAL;
            if(row == 100 && col == 100) val = 1023;
            if(row == 100 && col == 101) val = 1023/2;
            
            if(val != pixbuf[row][col])
            {
                lg->error("data mismatch at [{},{}], must be: {}, got: {}", row, col, val, pixbuf[row][col]);
                return;
            }
        }
    }
}
//------------------------------------------------------------------------------

