from .tests import test_tr
from ..message import err_msg, bcolors

import argparse
import signal
from datetime import datetime
import sys

import pickle
from collections import defaultdict
import sys
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

# Get color to work.
if os.name == "nt":
    os.system("color")

print(dask.__file__)

extension_path = "/home/bencarver/functions_kernel2/build/src/extensions/py_func_client"
sys.path.append(extension_path)
sys.path.append("/home/bencarver/functions_kernel2/build/src/extensions/py_invocation_return/")
pprint.pprint(sys.path)
# import func_client
import invocation_return

try:
    cluster = LocalCluster(
        num_lambda_invokers=1,
        initial_payload_batch_size=32)
except Exception as ex:
    print(err_msg("[ERROR] Failed to create and/or start Wukong LocalCluster..."))
    print(err_msg(ex))
    exit(1)

try:
    client = Client(cluster)  # set up local cluster on your laptop
except Exception as ex:
    print(err_msg("[ERROR] Failed to create and/or start Wukong Client."))
    print(err_msg(ex))
    exit(1)


def signal_handler(sig, frame):
    print(bcolors.WARNING + 'You pressed Ctrl+C!' + bcolors.ENDC)
    client.close()
    cluster.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

test_tr(64, 1, single_root_node=False, num_warmup_trials=0, sleep_interval=0, plot_dag=False, output_dir=None)

client.close()
cluster.close()
