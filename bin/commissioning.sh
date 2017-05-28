#!/bin/bash
cd `dirname $(readlink -f $0)`
ipython -i commissioning.py
