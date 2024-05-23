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


class MatrixMultiplicationExperiment(WukongExperiment):
    aliases: list[str] = ["matrix-multiplication", "mat-mul", "matmul"]
    experiment_name:str = "gemm"

    @staticmethod
    def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Create and add a sub-parser consisting of the tree-reduction-specific commandline arguments
        """
        parser = subparsers.add_parser(MatrixMultiplicationExperiment.experiment_name, description='Execute the "Tall-and-Skinny" GEMM workload',
                                       help='Execute the "Tall-and-Skinny" GEMM workload', aliases=MatrixMultiplicationExperiment.aliases)

        parser.add_argument("-m1d1", "--matrix1-dimension1", type=int, default=500,
                            help="First dimension of the first input array.")
        parser.add_argument("-m1d2", "--matrix1-dimension2", type=int, default=500,
                            help="Second dimension of the second input array.")

        parser.add_argument("-m2d1", "--matrix2-dimension1", type=int, default=500,
                            help="First dimension of the first input array.")
        parser.add_argument("-m2d2", "--matrix2-dimension2", type=int, default=500,
                            help="Second dimension of the second input array.")

        parser.add_argument("-m1c1", "--matrix1-chunk-dimension1", type=int, default=100,
                            help="First dimension of the chunk parameter of the first input array. Default: 1,000")
        parser.add_argument("-m1c2", "--matrix1-chunk-dimension2", type=int, default=100,
                            help="Second dimension of the chunk parameter of the first input array. Default: 100")

        parser.add_argument("-m2c1", "--matrix2-chunk-dimension1", type=int, default=100,
                            help="First dimension of the chunk parameter of the second input array. Default: 1,000")
        parser.add_argument("-m2c2", "--matrix2-chunk-dimension2", type=int, default=100,
                            help="Second dimension of the chunk parameter of the second input array. Default: 100")

        return parser

    def __init__(self, args: argparse.Namespace):
        self.m1_dimension1 = getattr(args, "matrix1_dimension1", 500)
        self.m1_dimension2 = getattr(args, "matrix1_dimension2", 500)

        self.m2_dimension1 = getattr(args, "matrix2_dimension1", 500)
        self.m2_dimension2 = getattr(args, "matrix2_dimension2", 500)

        self.m1_chunk_dimension1 = getattr(args, "matrix1_chunk_dimension1", 250)
        self.m1_chunk_dimension2 = getattr(args, "matrix1_chunk_dimension2", 250)

        self.m2_chunk_dimension1 = getattr(args, "matrix2_chunk_dimension1", 250)
        self.m2_chunk_dimension2 = getattr(args, "matrix2_chunk_dimension2", 250)

        super().__init__(MatrixMultiplicationExperiment.experiment_name, MatrixMultiplicationExperiment.aliases, args)

    def get_input_size_as_str(self) -> str:
        return "(%dx%d) x (%dx%d)" % (self.m1_dimension1, self.m1_dimension2, self.m2_dimension1, self.m2_dimension2)

    def execute(self):
        x = da.random.random((self.m1_dimension1, self.m1_dimension2), chunks=(self.m1_chunk_dimension1, self.m1_chunk_dimension2))
        y = da.random.random((self.m2_dimension1, self.m2_dimension2), chunks=(self.m2_chunk_dimension1, self.m2_chunk_dimension2))
        z = da.matmul(x, y)

        logger.debug(info_msg1("Submitting GEMM workload of now."))

        res = z.compute(scheduler=self._client.get)

        print("Result of GEMM:\n%s" % str(res))

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
