#!/bin/sh

multitail --config .config/multitail.conf -cS pylogger log/sdcam.log -cS spdlogger log/vframe.log