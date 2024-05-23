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


class LinearDAGExperiment(WukongExperiment):
    aliases: list[str] = ["linear_dag", "linear-dag"]
    experiment_name: str = "linear"

    @staticmethod
    def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
        """
        Create and add a sub-parser consisting of the tree-reduction-specific commandline arguments
        """
        parser = subparsers.add_parser(LinearDAGExperiment.experiment_name, description='Execute the "Linear DAG" workload',
                                       help='Execute the "Linear DAG" workload', aliases=LinearDAGExperiment.aliases)

        parser.add_argument("-l", "--dag-length", dest="dag_length", type=int,
                            default=1, help="How many tasks in the linear input DAG")
        parser.add_argument("--sleep-interval", dest="sleep_interval", type=float,
                            default=0, help="Sleep added to TR 'incr' operations (in seconds).")

        return parser

    def __init__(self, args: argparse.Namespace):
        self._dag_length = getattr(args, "dag_length", 1)
        self._sleep_interval: int = getattr(args, "sleep_interval", 0)

        super().__init__(LinearDAGExperiment.experiment_name, LinearDAGExperiment.aliases, args)

    def get_input_size_as_str(self) -> str:
        """
        Return the input size to the experiment formatted as a string.

        This exists because different experiments use different command line arguments to specify their input size.
        We use the experiment's input size when auto-generating the output directory for the experiment.
        """
        return str(self._dag_length)

    def execute(self):
        sleep_interval: int = self._sleep_interval

        def increment(x: int | float) -> int | float:
            time.sleep(sleep_interval)
            return x + 1

        inc = delayed(increment)

        """
        This is to be implemented by child classes. This actually runs the experiment's code.

        This function should not be called directly; instead, the entrypoint for all experiments is the `run_experiment` function.
        The `run_experiment` function will call the `execute` function.
        """
        for _ in range(self.num_trials + self.num_warmup_trials):
            leaf_task = inc(0)
            tmp = leaf_task
            num_tasks = 1

            for _ in range(0, self._dag_length - 1):
                next_task = inc(tmp)
                tmp = next_task
                num_tasks += 1

            print(tmp, flush=True)

            start_time = time.time()
            # res = self._client.compute(tmp)
            res = tmp.compute(scheduler=self._client.get)
            end_time = time.time()
            duration_sec = end_time - start_time

            print("\n\nExecuted linear path DAG consisting of %d tasks in %f seconds." %
                  (self._dag_length, duration_sec), flush=True)
            print("Total number of tasks executed: %d" % num_tasks, flush=True)
            print("Result of linear DAG workload: %s\n" % str(res), flush=True)
            time.sleep(0.100)

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
