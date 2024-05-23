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


class SingularVectorDecompositionCompressedExperiment(WukongExperiment):
    aliases: list[str] = ["svd-compressed"]
    experiment_name:str = "svd2"

    """
    This corresponds to "SVD of 'Tall-and-Skinny' Matrix".
    https://github.com/ds2-lab/Wukong/tree/socc2020?tab=readme-ov-file#svd-of-tall-and-skinny-matrix
    """
    @staticmethod
    def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Create and add a sub-parser consisting of the tree-reduction-specific commandline arguments
        """
        parser = subparsers.add_parser(SingularVectorDecompositionCompressedExperiment.experiment_name, description='Execute the "Tall-and-Skinny" SVD workload',
                                       help='Execute the "Tall-and-Skinny" SVD workload', aliases=SingularVectorDecompositionCompressedExperiment.aliases)

        parser.add_argument("-d1", "--dimension1", type=int, default=20000, help="First dimension of the input array.")
        parser.add_argument("-d2", "--dimension2", type=int, default=100, help="Second dimension of the input array.")

        parser.add_argument("-c1", "--chunk-dimension1", type=int, default=1000,
                            help="First dimension of the chunk parameter. Default: 1,000")
        parser.add_argument("-c2", "--chunk-dimension2", type=int, default=100,
                            help="Second dimension of the chunk parameter. Default: 100")

        parser.add_argument("-k", "--rank", type=int, default=5,
                            help="Rank of the desired thin SVD decomposition. Default: 5")

        return parser

    def __init__(self, args: argparse.Namespace):
        self.dimension1 = getattr(args, "dimension1", 20000)
        self.dimension2 = getattr(args, "dimension2", 100)

        self.chunk_dimension1 = getattr(args, "chunk_dimension1", 1000)
        self.chunk_dimension2 = getattr(args, "chunk_dimension2", 100)

        self.k = getattr(args, "k", 5)

        super().__init__(SingularVectorDecompositionCompressedExperiment.experiment_name, SingularVectorDecompositionCompressedExperiment.aliases, args)

    def get_input_size_as_str(self) -> str:
        return "%dx%d" % (self.dimension1, self.dimension2)

    def execute(self):
        # Compute the SVD of 'Tall-and-Skinny' Matrix
        X = da.random.random((self.dimension1, self.dimension2), chunks=(self.chunk_dimension1, self.chunk_dimension2))
        _, _, v = da.linalg.svd_compressed(X, self.k)

        logger.debug(info_msg1("Submitting SVD1 (tall-and-skinny) workload of %d x %d (%d x %d chunks) now." %
                     (self.dimension1, self.dimension2, self.chunk_dimension1, self.chunk_dimension2)))

        res = v.compute(scheduler=self._client.get)

        print("Result of SVD:\n%s" % str(res))

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
