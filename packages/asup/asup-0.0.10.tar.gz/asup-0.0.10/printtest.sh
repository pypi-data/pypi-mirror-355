#!/bin/bash
export BROTHER_QL_PRINTER=tcp://192.168.1.107:9100
export BROTHER_QL_MODEL=QL-820NWB
brother_ql print -l 62 --red ~/Downloads/dither_it_hulkog.png
