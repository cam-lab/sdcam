

#include "qpipe_cfg.h"

//------------------------------------------------------------------------------
int qpipe_cfg(TPipeRxParams &p)
{
    p.pipeRxNotifyFunc = 0;
    
    return static_cast<int>(createPipeViewRx(p));
}
//------------------------------------------------------------------------------
int qpipe_read_data(TVFrame &f, TPipeRxParams &p)
{
    TPipeRxTransfer t;
    t.pipeKey = p.pipeKey;
    t.dataBuf = f.raw_buf();
    t.dataLen = f.raw_buf_len();
    
//    std::cout << "data len: " << t.dataLen << std::endl;
    
    return static_cast<int>( readData(t) );
}
//------------------------------------------------------------------------------
//  typedef bool (*RxTransferFunc)(void* obj, uint8_t* src, uint32_t len);
//  struct TPipeRxTransferFuncObj
//  {
//      unsigned       pipeKey;
//      RxTransferFunc transferFunc;
//      void*          obj;
//
//      //--- DEBUG
//      uint32_t dataLen;
//  };

int qpipe_get_frame(TVFrame &f, TPipeRxParams &p)
{
    TPipeRxTransferFuncObj t;
    t.pipeKey = p.pipeKey;
    t.transferFunc = &deserialize_frame;
    t.obj          = &f;
    
    return static_cast<int>( readDataFuncObj(t) );
}
//------------------------------------------------------------------------------
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
//------------------------------------------------------------------------------
std::string pipe_info_repr(TPipeInfo & r)
{   
    std::stringstream out;
    out << "class 'PipeInfo': { " << std::endl << pipe_info_str(r, "  ") << "}";
    return out.str();
}
//------------------------------------------------------------------------------
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
//------------------------------------------------------------------------------
std::string pipe_rx_params_repr(TPipeRxParams & r)
{
    std::stringstream out;
    out << "class 'PipeRxParams': { " << std::endl << pipe_rx_params_str(r) << "}";
    return out.str();
}
//------------------------------------------------------------------------------

