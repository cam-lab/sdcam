
#ifndef QPIPE_CFG_H
#define QPIPE_CFG_H

#include <stdint.h>
#include <iostream>
#include <sstream>

#include <ip_qpipe_def.h>

using namespace IP_QPIPE_LIB;

//------------------------------------------------------------------------------
std::string pipe_info_str       (TPipeInfo& r, std::string offset);
std::string pipe_info_repr      (TPipeInfo& r);
std::string pipe_rx_params_str  (TPipeRxParams& r);
std::string pipe_rx_params_repr (TPipeRxParams& r);
void        pipe_rx_params      (TPipeRxParams *p);
//------------------------------------------------------------------------------
#endif // QPIPE_CFG_H

