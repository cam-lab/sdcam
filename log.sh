#!/bin/bash

if [[ $1 == "py" ]]; then
    multitail --config .config/multitail.conf -cS pylogger log/sdcam.log

elif [[ $1 == "cpp" ]]; then
    multitail --config .config/multitail.conf -cS spdlogger log/vframe.log
else
    multitail --config .config/multitail.conf -cS pylogger log/sdcam.log -cS spdlogger log/vframe.log
fi

