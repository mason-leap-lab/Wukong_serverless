from .experiment import WukongExperiment
from wukong.testing.experiments import TreeReductionExperiment
from wukong.testing.experiments import LinearDAGExperiment
from wukong.testing.experiments import SingularVectorDecompositionExperiment
from wukong.testing.experiments import TSQRExperiment

import wukong.testing.experiments as experiments_module

import argparse
import socket 

# Dynamically discover all experiments.
experiment_classes = list([cls for _, cls in experiments_module.__dict__.items() if isinstance(cls, type)])

def get_cmdline_args() -> argparse.Namespace:
    """
    Get the commandline arguments for the experiment. This includes both generic commandline 
    arguments that apply to all experiments and experiment-specific commandline arguments.
    """

    # Automatically resolve private ipv4.
    # You can set this manually if preferred/necessary.
    import socket 
    hostname = socket.getfqdn()
    private_ipv4 = socket.gethostbyname_ex(hostname)[2][0]

    # Create the generic parser for command line arguments that apply to all experiments.
    parent_parser: argparse.ArgumentParser = argparse.ArgumentParser()

    parent_parser.add_argument("--output-directory", dest="output_directory", type=str, default=None,
                                help="Directory into which experimental results will be written. If the empty string is specified, then results will be written to current directory. If None is specified, then an output directory will be generated automatically using the current date/time.")
    parent_parser.add_argument("--num-trials", dest="num_trials", type=int,
                                default=1, help="Number of repeated trials.")
    parent_parser.add_argument("--num-invokers", dest="num_invokers", type=int, default=8,
                                help="Number of invoker processes to use in Wukong's static scheduler.")
    parent_parser.add_argument("--no-metrics", dest="no_metrics", action='store_true',
                                help="If passed, then do not collect any task-level or serverless-function-level metrics from Wukong.")
    parent_parser.add_argument("--num-warmup-trials", type=int, dest='num_warmup_trials', default=0)
    parent_parser.add_argument("--wukong-config-file", dest="wukong_config_file",
                                default="wukong/wukong-config.yaml", help="Path to the Wukong configuration file.")
    parent_parser.add_argument("--scheduler-hostname", dest = "scheduler_hostname", type = str, default = private_ipv4, help = f"Hostname of the Static Scheduler. Default: {private_ipv4}")
    parent_parser.add_argument("--proxy-hostname", dest = "proxy_hostname", type = str, default = private_ipv4, help = f"Hostname of the KV Store Proxy. Default: {private_ipv4}")
    parent_parser.add_argument("--task-metrics-output-file", type = str, dest = "task_metrics_output_file", default = "task_metrics", help = "Output file path for task-level metrics. The file extension should be omitted, as this file path is used for both the pickle file and the CSV file.")
    parent_parser.add_argument("--lambda-metrics-output-file", type = str, dest = "lambda_metrics_output_file", default = "lambda_metrics", help = "Output file path for serverless-function-level metrics. The file extension should be omitted, as this file path is used for both the pickle file and the CSV file.")
    parent_parser.add_argument("--task-metrics-")
    
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser] = parent_parser.add_subparsers(dest = "run", title = "run", help = "Run an experiment.", required = True)
    parser_run = subparsers.add_parser("run", help = "Run an experiment.")
    experiment_subparsers = parser_run.add_subparsers(dest = "experiment_name", title = "Experiment Name", help = "Specify the name of the experiment to run", required = True)
    
    for experiment_class in experiment_classes:
        experiment_class.add_argument_parser(experiment_subparsers)

    args: argparse.Namespace = parent_parser.parse_args()

    return args

args: argparse.Namespace = get_cmdline_args()

print(args, flush=True)

requested_experiment_name = args.experiment_name
target_experiment: WukongExperiment = None
experiments = [experiment_class(args) for experiment_class in experiment_classes]

for experiment in experiments:
    if experiment.match_name(requested_experiment_name):
        target_experiment = experiment
        break 

if target_experiment == None:
    raise ValueError("UNEXPECTED: Invalid or unsupported experiment specified: \"%s\"" % requested_experiment_name)

target_experiment.run_experiment()
