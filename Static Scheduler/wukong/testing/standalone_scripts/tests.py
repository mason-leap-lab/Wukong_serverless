###
#
# Some sample/existing tests to use.
#
###

import argparse
import signal
from datetime import datetime
import sys

import matplotlib
import matplotlib.pyplot as plt
import subprocess

import pickle
from collections import defaultdict
import sys
import pandas as pd

import numpy as np
import pprint

import ujson

import dask
import dask.array as da
import time
from wukong.distributed import Client, LocalCluster, get_task_stream
from dask import delayed
import logging
import plotly.figure_factory as ff
import plotly as py
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logFormatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(logFormatter)

# Add console handler to logger
logger.addHandler(consoleHandler)


def test_tr(n, num_trials, single_root_node=False, num_warmup_trials=0, sleep_interval=0, plot_dag=False, output_dir=None):
    """
    'n' is the size of the array being reduced.

    'num_trials' is the number of trials.
    """
    add_functions = []
    FUNC_TEMPLATE = """def add_{0}(x,y): return x+y"""
    for x in range(0, 100):
        exec(FUNC_TEMPLATE.format(x))

    ADD_TEMPLATE = """add_functions.append(add_{0})"""
    for x in range(0, 100):
        exec(ADD_TEMPLATE.format(x))

    assert (num_trials > 0)
    assert (n > 0)
    logger.debug("[TEST DRIVER] Performing %d trials of tree reduction on an array of size %d." % (num_trials, n))
    results = []

    generated_dag = False

    # flamegraph.start_profile_thread(fd=open("./wukong.log", "w"))

    # logger.debug("Sleeping for 10 seconds before beginning the benchmark.")
    # time.sleep(10)

    def add_base(x, y, z):
        time.sleep(sleep_interval)
        return x + y

    def add_vals(x, y):
        time.sleep(sleep_interval)
        return x + y

    def incr(x):
        return x + 1

    workload_start_time = None  # time.time()
    for i in range(num_trials + num_warmup_trials):
        L = range(n)
        layer = 0
        first_layer_done = False
        first_task = delayed(incr)(0)
        counter = 0
        while len(L) > 1:
            if not first_layer_done and single_root_node:
                L_tmp = []
                L1 = list(L[0::2])
                L2 = list(L[1::2])
                for x, y in list(zip(L1, L2)):
                    task = delayed(add_base)(x, y, first_task)
                    L_tmp.append(task)

                first_layer_done = True
                L = L_tmp
            else:
                # Apply the 'add' operation to adjacent elements in the list 'L'
                L = list(map(delayed(add_functions[layer]), L[0::2], L[1::2]))
                layer += 1

        if plot_dag and not generated_dag:
            print("Generating low-level DAG.")
            L[0].visualize(filename='tr_%d_single_root_lowlevel.svg' % n)  # , optimize_graph=True)
            print("Generating high-level DAG.")
            L[0].dask.visualize(filename='tr_%d_single_root_highlevel.svg' % n)
            generated_dag = True

        logger.debug("[TEST DRIVER] Submitting TR workload (trial #%d) now..." % i)

        _start = time.time()
        if workload_start_time is None:
            workload_start_time = _start
        res = L[0].compute()
        time_elapsed = time.time() - _start
        logger.info("[TEST DRIVER] TR Trial #%d finished in %f seconds. Result: %s." % (i, time_elapsed, res))
        results.append(time_elapsed * 1.0e3)
        time.sleep(1.25)

    logger.info("Results: %s" % str(results))
    # Get rid of the warm-up trials.
    results = results[num_warmup_trials:]
    _avg = sum(results) / len(results)
    _min = min(results)
    _max = max(results)

    if not os.path.isdir("./output"):
        os.mkdir("./output")

    print("\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n[Tree Reduction (n=%d) End-to-End Times]" % n)
    print("Average: {0:,.4f} ms\nMin: {1:,.4f} ms\nMax: {2:,.4f} ms".format(_avg, _min, _max))
    print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n\n")

    if output_dir == None:
        now = datetime.now()
        dt_string = now.strftime("TR num_trials-%m-%Y %H:%M:%S")
        output_dir = os.path.join("./output", dt_string)

    print("Creating directory \"%s\"" % output_dir)
    os.mkdir(output_dir)

    data = {
        "raw": results,
        "avg": _avg,
        "min": _min,
        "max": _max,
        "problem": "tree reduction",
        "problem_size": n
    }

    results_filepath = os.path.join(output_dir, "data.json")
    with open(results_filepath, "w") as f:
        ujson.dump(data, f)

    print("Wrote results to file: \"%s\"" % results_filepath)

    return workload_start_time
