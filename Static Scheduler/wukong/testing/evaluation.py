import logging
import os
import time

from .message import info_msg1, info_msg2, success_msg, warn_msg, err_msg
from .experiment import WukongExperiment

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

# Get color to work.
if os.name == "nt":
    os.system("color")


class WukongEvaluation(object):
    """
    Main class for running an evaluation on Wukong.

    A WukongEvaluation consists of one or more experiments.
    
    Currently unused.
    """

    def __init__(self):
        pass
