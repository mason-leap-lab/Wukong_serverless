from wukong.testing.experiment import WukongExperiment
from wukong.testing.message import info_msg1, info_msg2, success_msg, warn_msg, err_msg

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

class TreeReductionExperiment(WukongExperiment):
    aliases:list[str] = ["tr", "tree-reduction"]
    experiment_name:str = "tree_reduction"
    
    @staticmethod
    def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Create and add a sub-parser consisting of the tree-reduction-specific commandline arguments
        """
        parser = subparsers.add_parser("TreeReductionExperiment.experiment_name", description='Execute the "tree reduction" workload', help='Execute the "tree reduction" workload', aliases=TreeReductionExperiment.aliases)

        parser.add_argument("--single-root-node", dest='single_root_node', action='store_true', default = False)
        parser.add_argument("--sleep-interval", dest="sleep_interval", type=float,
                            default=0, help="Sleep added to TR 'add' operations (in seconds).")
        parser.add_argument("--input-size", dest="input_size", type=int, default=128,
                            help="Size of the input array on which the tree reduction is performed.")

        return parser

    def __init__(self, args: argparse.Namespace):        
        self._n = getattr(args, "input_size", 0)
        self._single_root_node = getattr(args, "single_root_node", False)

        super().__init__("TreeReductionExperiment.experiment_name", TreeReductionExperiment.aliases, args)
    
    def get_input_size_as_str(self)->str:
        return str(self._n)

    def execute(self):
        def increment(x: int | float) -> int | float:
            return x + 1

        def add(x: int | float, y: int | float) -> int | float:
            return x + y

        add_functions = []
        FUNC_TEMPLATE = """def add_{0}(x,y): return x+y"""
        for x in range(0, 100):
            exec(FUNC_TEMPLATE.format(x))

        ADD_TEMPLATE = """add_functions.append(add_{0})"""
        for x in range(0, 100):
            exec(ADD_TEMPLATE.format(x))

        """
        This is to be implemented by child classes. This actually runs the experiment's code.

        This function should not be called directly; instead, the entrypoint for all experiments is the `run_experiment` function.
        The `run_experiment` function will call the `execute` function.
        """
        L = range(self._n)
        layer = 0
        first_layer_done = False
        first_task = delayed(increment)(0)
        while len(L) > 1:
            if not first_layer_done and self._single_root_node:
                L_tmp = []
                L1 = list(L[0::2])
                L2 = list(L[1::2])
                for x, y in list(zip(L1, L2)):
                    task = delayed(add)(x, y, first_task)
                    L_tmp.append(task)

                first_layer_done = True
                L = L_tmp
            else:
                # Apply the 'add' operation to adjacent elements in the list 'L'
                L = list(map(delayed(add_functions[layer]), L[0::2], L[1::2]))
                layer += 1

        if self.plot_dag and not generated_dag:
            print("Generating low-level DAG.")
            L[0].visualize(filename='tr_%d_single_root_lowlevel.svg' % self._n)  # , optimize_graph=True)
            print("Generating high-level DAG.")
            L[0].dask.visualize(filename='tr_%d_single_root_highlevel.svg' % self._n)
            generated_dag = True

        logger.debug(info_msg1("Submitting TR workload now..."))

        res = L[0].compute(scheduler = self._client.get)
        
        logger.debug("Result of TR workload: %s" % str(res))

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
