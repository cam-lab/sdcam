
#ifndef QPIPE_CFG_H
#define QPIPE_CFG_H

#include <stdint.h>
#include <iostream>
#include <sstream>

#include "vframe.h"

#include <ip_qpipe_def.h>
#include <ip_qpipe_lib.h>

using namespace IP_QPIPE_LIB;

//------------------------------------------------------------------------------
std::string pipe_info_str       (TPipeInfo& r, std::string offset);
std::string pipe_info_repr      (TPipeInfo& r);
std::string pipe_rx_params_str  (TPipeRxParams& r);
std::string pipe_rx_params_repr (TPipeRxParams& r);
int         qpipe_cfg           (TPipeRxParams& p);
int         qpipe_read_data     (TVFrame &f, TPipeRxParams &p);
int         qpipe_get_frame     (TVFrame &f, TPipeRxParams &p);

//------------------------------------------------------------------------------
#endif // QPIPE_CFG_H

