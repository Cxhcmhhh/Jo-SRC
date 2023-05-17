#!/usr/bin/env bash

export PYTHONWARNINGS="ignore"
export GPU=0
python main.py --config config/noisylabeln.cfg --gpu ${GPU}