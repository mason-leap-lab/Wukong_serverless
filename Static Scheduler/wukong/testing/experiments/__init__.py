from .tree_reduction import TreeReductionExperiment
from .linear_dag import LinearDAGExperiment
from .svd1 import SingularVectorDecompositionExperiment
from .svd2 import SingularVectorDecompositionCompressedExperiment
from .tsqr import TSQRExperiment
from .generate_random_array import GenerateRandomArrayExperiment
from .gemm import MatrixMultiplicationExperiment

"""
This module contains custom-defined experiments.

Any classes in this module MUST subclass the base WukongExperiment class defined in the wukong/testing/experiment.py file.

After creating the new experiment class, add its import above.
"""
