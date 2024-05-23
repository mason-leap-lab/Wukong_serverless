from wukong.testing.experiment import WukongExperiment
from wukong.testing.message import info_msg1, info_msg2, success_msg, warn_msg, err_msg
from wukong.distributed.protocol.serialize import Serialized

import dask.array as da

from dask import delayed

import argparse
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)


class TSQRExperiment(WukongExperiment):
    aliases: list[str] = ["tall-and-skinny-qr-reduction"]
    experiment_name:str = "tsqr"

    """
    This corresponds to "'Tall-and-Skinny' QR Reduction" (TSQR).
    https://github.com/ds2-lab/Wukong/blob/249aa99517aaff60c049906eaba41767fb39c864/docs/examples/examples.rst#tall-and-skinny-qr-reduction-tsqr
    """
    @staticmethod
    def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Create and add a sub-parser consisting of the tree-reduction-specific commandline arguments
        """
        parser = subparsers.add_parser(TSQRExperiment.experiment_name, description='Execute the "Tall-and-Skinny" QR reduction (TSQR) workload',
                                       help='Execute the "Tall-and-Skinny" QR reduction (TSQR) workload', aliases=TSQRExperiment.aliases)

        parser.add_argument("-d1", "--dimension1", type=int, default=262_144,
                            help="First dimension of the input array.")
        parser.add_argument("-d2", "--dimension2", type=int, default=128, help="Second dimension of the input array.")

        parser.add_argument("-c1", "--chunk-dimension1", type=int, default=8192,
                            help="First dimension of the chunk parameter.")
        parser.add_argument("-c2", "--chunk-dimension2", type=int, default=128,
                            help="Second dimension of the chunk parameter.")

        return parser

    def __init__(self, args: argparse.Namespace):
        self.dimension1 = getattr(args, "dimension1", 262_144)
        self.dimension2 = getattr(args, "dimension2", 128)

        self.chunk_dimension1 = getattr(args, "chunk_dimension1", 8192)
        self.chunk_dimension2 = getattr(args, "chunk_dimension2", 128)

        super().__init__(TSQRExperiment.experiment_name, TSQRExperiment.aliases, args)

    def get_input_size_as_str(self) -> str:
        return "%dx%d" % (self.dimension1, self.dimension2)

    def execute(self):
        X = da.random.random((262_144, 128), chunks=(8192, 128))
        _, r = da.linalg.tsqr(X)

        logger.debug(info_msg1("Submitting TSQR workload now..."))

        res = r.compute(scheduler=self._client.get)

        print("Result of TSQR:\n%s" % str(res))

    def prepare(self):
        """
        This is to be implemented by child classes. This performs any experiment-specific setup, such as creating certain files or directories.

        This function should not be called directly.
        """
        # No preparation required for tree reduction.
        pass

    def cleanup(self):
        """
        This is to be implemented by child classes. This performs any experiment-specific clean-up. 

        This function should not be called directly.
        """
        # No clean-up required for tree reduction.
        pass
