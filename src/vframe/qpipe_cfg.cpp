

#include "qpipe_cfg.h"

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

