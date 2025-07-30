#!/bin/bash
python3 mp_process.py --pid 0 --num_worker 8 &
python3 mp_process.py --pid 1 --num_worker 8 &
python3 mp_process.py --pid 2 --num_worker 8 &
python3 mp_process.py --pid 3 --num_worker 8 &
python3 mp_process.py --pid 4 --num_worker 8 &
python3 mp_process.py --pid 5 --num_worker 8 &
python3 mp_process.py --pid 6 --num_worker 8 &
python3 mp_process.py --pid 7 --num_worker 8 &
