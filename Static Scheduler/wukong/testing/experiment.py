from abc import ABC, abstractmethod
import argparse
import datetime
import logging
import os
import sys
import time
import pickle
import pandas as pd
import numpy as np

from wukong.distributed import LocalCluster, Client
from wukong.visualization.visualization import plot_execution_breakdown, extract_wukong_events_from_lambda_metrics, lambda_metrics_to_csv, task_metrics_to_csv, plot_specific_kv_op_breakdown, plot_highlevel_kv_breakdown
from .message import info_msg1, info_msg2, success_msg, warn_msg, err_msg

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

class WukongExperiment(ABC):
    # Other valid names for the experiment.
    # Subclasses should provide their own aliases variable.
    aliases: list[str] = [] 
    
    @staticmethod
    def get_arg(args: argparse.Namespace, arg_name: str, default_value):
        return getattr(args, arg_name, default_value)

    def __init__(self, name: str, aliases: list[str], args: argparse.Namespace):
        """
        Arguments:
            - name(str): The name of the experiment.
            - output_directory(str): The fully-qualified path in which the experiment's output should be written.
        """
        # The name of the experiment.
        self._name: str = name
        self._aliases: list[str] = aliases,
        self._args = args._get_kwargs()

        # The directory to which any results will be written.
        # IMPORTANT: If either `None` or the empty string are specified, then no output will be generated.
        self._output_directory: str = args.output_directory

        # Number of repeated trials.
        self.num_trials: int = args.num_trials
        
        self.scheduler_hostname:str = args.scheduler_hostname
        self.proxy_hostname:str = args.proxy_hostname

        # Number of threads to use to invoke serverless functions (at the C++ level).
        self.num_invokers: int = args.num_invokers

        # Number of trials to run before conducting the actual experiment.
        self.num_warmup_trials: int = args.num_warmup_trials

        # The start-time of the experiment; initialized to -1. It is set to the actual start time when the `run_experiment` method is called.
        self._start_time: float = -1

        # Path to the Wukong configuration file.
        self._wukong_config_file = args.wukong_config_file

        # The start-time of the experiment; initialized to -1. It is set to the actual end time right before the `run_experiment` method returns.
        self._end_time: float = -1

        # The end-to-end duration, in seconds, of the entire experiment, including all repeated trials.
        # This is initialized to -1. It is set to the end-to-end duration right before the `run_experiment` method returns.
        self._experiment_duration: float = -1

        # End-to-end latencies of each trial.
        self._latencies: list[float] = []

        # Indicates whether the experiment has been completed or not yet.
        self._complete = False

        # Output file path for task-level metrics.
        self._task_metrics_output_file: str = args.task_metrics_output_file

        # Output file path for serverless-function-level metrics.
        self._lambda_metrics_output_file: str = args.lambda_metrics_output_file

    def __shutdown(self) -> None:
        """
        Internal method that cleans up resources.
        """
        self._client.close()
        self._cluster.close()

    def __setup(self) -> None:
        """
        Internal setup method that is used by all experiments. This runs before the experiment-specific setup.

        If either the LocalCluster or the Client fail to be created (i.e., an exception is thrown during their creation),
        then this function will essentially panic and terminate the entire application.
        """
        logger.debug(info_msg1("Performing internal experiment setup now..."))
        st = time.time()

        self.try_create_output_directory()

        try:
            self._cluster = LocalCluster(
                host=self.scheduler_hostname,
                proxy_address=self.proxy_hostname, 
                num_lambda_invokers = 2, 
                use_local_proxy = False, 
                redis_endpoints = [(self.scheduler_hostname, 6379)], 
                use_fargate = False)
        except Exception as ex:
            logger.error(err_msg("Failed to create and/or start Wukong LocalCluster."))
            logger.error(err_msg(ex))
            exit(1)

        try:
            self._client = Client(self._cluster)  # set up local cluster on your laptop
        except Exception as ex:
            logger.error(err_msg("Failed to create and/or start Wukong Client."))
            logger.error(err_msg(ex))
            exit(1)

        logger.debug(info_msg1("Internal experiment setup completed successfully in %.4f seconds." % (time.time() - st)))

    def match_name(self, name: str) -> bool:
        """
        Return true if the given name matches the experiment's name or one of its aliases.
        """
        return self.name == name or name in self.aliases

    def add_latency(self, latency: float) -> None:
        self._latencies.append(latency)

    @property
    def latencies(self) -> list[float]:
        """
        Return the end-to-end latencies of each trial.
        """
        return self._latencies

    @property
    def client(self) -> Client:
        """
        Return the Wukong Client used by this experiment.
        """
        return self._client

    @property
    def local_cluster(self) -> LocalCluster:
        """
        Return the Wukong LocalCluster used by this experiment.

        The LocalCluster consists only of the Wukong Scheduler.
        """
        return self._cluster

    @property
    def start_time(self) -> str:
        """
        Return the time at which the actual experiment started (not including setup, cleanup, etc.).

        The time is represented as the time in seconds since the epoch (from when the experiment started).
        """
        return self._start_time

    @property
    def end_time(self) -> str:
        """
        Return the time at which the actual experiment completed (not including setup, cleanup, etc.).

        The time is represented as the time in seconds since the epoch (from when the experiment completed).
        """
        return self._end_time

    @property
    def total_duration(self) -> str:
        """
        Return the total duration of the actual experiment in seconds (not including setup, cleanup, etc.).
        """
        return self._experiment_duration

    @property
    def aliases(self) -> list[str]:
        return self._aliases

    @property
    def name(self) -> str:
        """
        Return the experiment's name.
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """
        Set/update the experiment's name.
        """
        self._name = value

    @property
    def output_directory(self) -> str:
        """
        Return the output directory that has been configured for the experiment.
        """
        return self._output_directory

    @output_directory.setter
    def output_directory(self, value: str):
        """
        Set/update the output directory that has been configured for the experiment.
        """
        self._output_directory = value

    @property
    def complete(self) -> bool:
        """
        Return True if the experiment has been executed.
        """
        return self._complete

    def _get_output_path(self, filename: str) -> str:
        """
        Return the full filepath for a particular output file.

        Basically, prepend the output directory.
        """
        if self._output_to_current_working_directory:
            return filename
        else:
            return os.path.join(self.output_directory, filename)

    def load_metrics(self, task_metrics_output_file: str = "./task_breakdowns.pkl", lambda_metrics_output_file: str = "./lambda_breakdowns.pkl"):
        """
        Load the metrics after the experiment has finished.

        If the experiment has not been executed yet, or if metrics are disabled, then this returns None.

        If the output path parameter is None or the empty string, then the associated metrics are not written to a file.
        """
        if not self.complete or self.no_metrics:
            logger.info("Cannot retrieve metrics. Experiment is either not finished or metrics were disabled.")
            return None

        logger.info("Retrieving metrics for experiment %s now.", self.name)
        task_breakdowns = self._cluster.scheduler.get_task_breakdowns(i=-1, j=-1)
        lambda_breakdowns = self._cluster.scheduler.get_lambda_breakdowns(i=-1, j=-1)

        # Parse metrics.
        df = extract_wukong_events_from_lambda_metrics(lambda_breakdowns)

        logger.info("Number of Lambda Breakdowns retrieved: %d" % len(lambda_breakdowns))

        # Write pickled task-level metrics to a file.
        if task_metrics_output_file is not None and len(task_metrics_output_file) > 0:
            task_metrics_output_pickle_file = self._get_output_path(task_metrics_output_file + ".pkl")

            with open(task_metrics_output_pickle_file, 'wb') as f:
                pickle.dump(task_breakdowns, f)
                logger.info("Wrote task-level metrics to file \"%s\"" % task_metrics_output_pickle_file)

            task_metrics_output_csv = self._get_output_path(task_metrics_output_file + ".csv")
            task_metrics_to_csv(task_metrics_output_csv, task_breakdowns)
        else:
            logger.warn("Skipping the writing of task-level metrics to a file (output path is None or the empty string).")

        # Write pickled serverless-function-level metrics to a file.
        if lambda_metrics_output_file is not None and len(lambda_metrics_output_file) > 0:
            lambda_metrics_output_pickle_file = self._get_output_path(lambda_metrics_output_file + ".pkl")

            with open(lambda_metrics_output_pickle_file, 'wb') as f:
                pickle.dump(lambda_breakdowns, f)
                logger.info("Wrote task-level metrics to file \"%s\"" % lambda_metrics_output_pickle_file)

            lambda_metrics_output_csv = self._get_output_path(lambda_metrics_output_file + "-parsed.csv")
            df.to_csv(lambda_metrics_output_csv)

            lambda_metrics_output_csv = self._get_output_path(lambda_metrics_output_file + ".csv")
            lambda_metrics_to_csv(lambda_metrics_output_csv, lambda_breakdowns)
            lambda_df: pd.DataFrame = pd.read_csv(lambda_metrics_output_csv, delimiter=';')
        else:
            logger.warn(
                "Skipping the writing of serverless-function-level metrics to a file (output path is None or the empty string).")
            lambda_df = None

        plot_execution_breakdown(df=df, output_file=self._get_output_path(
            "execution_breakdown"), plot_title="{name} {problem_size} Breakdown".format(name=self.name, problem_size=self.get_input_size_as_str()))

        if lambda_df is not None:
            plot_specific_kv_op_breakdown(df=lambda_df, output_file=self._get_output_path(
                "specific_kv_op_breakdown"), plot_title="{name} {problem_size} KV Ops".format(name=self.name, problem_size=self.get_input_size_as_str()))
            plot_highlevel_kv_breakdown(df=lambda_df, output_file=self._get_output_path(
                "high_level_kv_breakdown"), plot_title="{name} {problem_size} Highlevel KV".format(name=self.name, problem_size=self.get_input_size_as_str()))

        grouped_df = df.groupby("event_name")
        events: list[str] = list(grouped_df.groups.keys())

        with open(self._get_output_path("metrics_summary.txt"), "w") as f:
            for event_name in events:
                group = grouped_df.get_group(event_name)
                avg = group["duration"].mean()
                total = group["duration"].sum()
                logger.info("Average %s: %.8f sec" % (event_name, avg))
                logger.info("Total %s: %.8f sec" % (event_name, total))
                f.write("Average %s: %.8f sec\n" % (event_name, avg))
                f.write("Total %s: %.8f sec\n" % (event_name, total))

        logger.info("End-to-end Latencies:")
        with open(self._get_output_path("e2e_latency.csv"), "w") as f:
            f.write("trial,latency\n")
            for idx, latency in enumerate(self._latencies):
                logger.info("Trial #%d: %.4f ms" % (idx + 1, latency))
                f.write("%d,%s\n" % (idx, latency))

        logger.info("Average latency: %.4f ms" % (sum(self._latencies) / len(self._latencies)))
        logger.info("Sum of trial latencies: %.4f ms" % sum(self._latencies))
        logger.info("Min latency: %.4f ms" % min(self._latencies))
        logger.info("Max latency: %.4f ms" % max(self._latencies))

        return task_breakdowns, lambda_breakdowns

    def run_experiment(self) -> None:
        """
        This is the entrypoint for all experiments.

        This function calls certain abstract methods in this order:
        - (1) prepare
        - (2) execute
        - (3) cleanup

        This function does not return anything.
        """
        experiment_start: float = time.time()
        self.__setup()

        logger.debug(info_msg1("Preparing experiment \"%s\" now..." % self.name))
        st = time.time()
        try:
            self.prepare()
        except Exception as ex:
            logger.error(err_msg("Error encountered while preparing for experiment \"%s\"" % self.name))
            logger.error(err_msg(ex))
            return

        logger.debug(info_msg2("Finished preparing experiment \"%s\" in %.4f seconds" % (self.name, time.time() - st)))
        logger.debug(info_msg1("Executing experiment \"%s\" now..." % self.name))
        self._start_time = time.time()

        st = time.time()

        try:
            for i in range(self.num_warmup_trials):
                logger.debug("Executing warm-up trial %d of %d of experiment \"%s\" now..." %
                             (i, self.num_warmup_trials, self.name))
                trial_start_time: float = time.time()
                self.execute()
                trial_end_time: float = time.time()
                trial_duration = trial_end_time - trial_start_time
                logger.debug("Completed warm-up trial %d of %d of experiment \"%s\" in %.4f seconds." %
                             (i, self.num_warmup_trials, self.name, trial_duration))
        except Exception as ex:
            logger.error(err_msg("Error encountered while executing experiment \"%s\"" % self.name))
            logger.error(err_msg(ex))
            raise ex

        try:
            for i in range(self.num_trials):
                logger.debug("Executing trial %d of %d of experiment \"%s\" now..." % (i, self.num_trials, self.name))
                trial_start_time: float = time.time()
                self.execute()
                trial_end_time: float = time.time()
                trial_duration = trial_end_time - trial_start_time
                logger.debug("Completed trial %d of %d of experiment \"%s\" in %.4f seconds." %
                             (i, self.num_trials, self.name, trial_duration))

                self.add_latency(trial_duration * 1.0e3)
                time.sleep(1.25)
        except Exception as ex:
            logger.error(err_msg("Error encountered while executing experiment \"%s\"" % self.name))
            logger.error(err_msg(ex))
            raise ex

        self._end_time = time.time()
        self._experiment_duration = self._end_time - self._start_time

        logger.debug(success_msg("Finished executing experiment \"%s\" in %.4f seconds" % (self.name, time.time() - st)))
        self._complete = True
        self.load_metrics(task_metrics_output_file=self._task_metrics_output_file,
                          lambda_metrics_output_file=self._lambda_metrics_output_file)
        logger.debug(info_msg1("Cleaning up experiment \"%s\" now..." % self.name))
        st = time.time()
        try:
            self.cleanup()
        except Exception as ex:
            logger.error(err_msg("Error encountered while cleaning-up experiment \"%s\"" % self.name))
            logger.error(err_msg(ex))
            return

        self.experiment_end: float = time.time()
        total_duration: float = self.experiment_end - experiment_start

        logger.debug(info_msg2("Finished cleaning up experiment \"%s\" in %.4f seconds" % (self.name, time.time() - st)))
        logger.debug(success_msg("Experiment \"%s\" has completed successfully. Total time elapsed: %.4f seconds. Experiment time: %.4f seconds." %
                     (self.name, total_duration, self._experiment_duration)))

        self.__shutdown()

    def try_create_output_directory(self):
        """
        Create the output directory for the experiment, if necessary.
        """
        if self.output_directory == "":
            logger.warn(
                "Output directory specified as the empty string. Output data will be written to the current working directory.")
            self._output_to_current_working_directory: bool = True
        elif self.output_directory == None:
            self._output_directory = './output/{name}-n={problem_size}-t={num_trials}-{date:%Y-%m-%d_%H-%M-%S}'.format(
                name=self.name, problem_size=self.get_input_size_as_str(), num_trials=self.num_trials, date=datetime.datetime.now())
            self._output_to_current_working_directory: bool = False
            os.makedirs(self._output_directory)

            logger.info("Experimental results will be written to auto-generated directory \"%s\"" %
                        self.output_directory)
        else:
            logger.info("Experimental results will be written to directory \"%s\"" % self.output_directory)
            self._output_to_current_working_directory: bool = False

        # Write the command used to run the experiment to a file.
        with open(self._get_output_path("command.txt"), "w") as f:
            f.write("%s %s" % (sys.executable, " ".join(sys.argv)))

    @abstractmethod
    def get_input_size_as_str(self) -> str:
        """
        Return the input size to the experiment formatted as a string.

        This exists because different experiments use different command line arguments to specify their input size.
        We use the experiment's input size when auto-generating the output directory for the experiment.
        """
        pass

    @abstractmethod
    def execute(self) -> list[float]:
        """
        This is to be implemented by child classes. This actually runs the experiment's code.

        This should run a single execution/trial of the experiment. Repeated trials will be called automatically.

        This function should not be called directly; instead, the entrypoint for all experiments is the `run_experiment` function.
        The `run_experiment` function will call the `execute` function.
        """
        pass

    @abstractmethod
    def prepare(self):
        """
        This is to be implemented by child classes. This performs any experiment-specific setup, such as creating certain files or directories.

        This function should not be called directly.
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        This is to be implemented by child classes. This performs any experiment-specific clean-up. 

        This function should not be called directly.
        """
        pass
