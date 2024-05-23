# Wukong `testing` Module

This module provides a streamlined system for creating and executing Wukong benchmarks and applications.

## Usage 

### Top-Level Arguments

The top-level arguments for the evaluation driver are shown below.

``` sh
python3 -m wukong.testing [-h] [--output-directory OUTPUT_DIRECTORY] [--num-trials NUM_TRIALS] 
                          [--plot-dag] [--num-invokers NUM_INVOKERS] [--batch-size BATCH_SIZE] 
                          [--plot-gantt] [--no-metrics] [--num-warmup-trials NUM_WARMUP_TRIALS] 
                          [--gantt-output-path GANTT_OUTPUT_PATH] 
                          [--wukong-config-file WUKONG_CONFIG_FILE] 
                          [--faas-hostname FAAS_HOSTNAME] [--faas-port FAAS_PORT] 
                          [--task-metrics-output-file TASK_METRICS_OUTPUT_FILE] 
                          [--lambda-metrics-output-file LAMBDA_METRICS_OUTPUT_FILE] 
                          [--task-metrics- TASK_METRICS_]
                        {run} ...
```
```
-h, --help            show this help message and exit
--output-directory OUTPUT_DIRECTORY
                    Directory into which experimental results will be written. 
                    If the empty string is specified, then results will be written to current directory. 
                    If None is specified, then an output directory will be generated automatically using the current date/time.
--num-trials NUM_TRIALS
                    Number of repeated trials.
--plot-dag            If true, then we will generate a visualization of the experiment's DAG and write it to the experiment's output directory. 
                    If no output directory is set, then this option is ignored.
--num-invokers NUM_INVOKERS
                    Number of invoker processes to use in Wukong's static scheduler.
--batch-size BATCH_SIZE
                    How many static schedules to store at-once in the KV store.
--plot-gantt          Plot a Gantt chart of the test's execution. Does nothing if `--no-metrics` is passed (as metrics are required for a Gantt chart to be created).
--no-metrics          If passed, then do not collect any task-level or serverless-function-level metrics from Wukong.
--num-warmup-trials NUM_WARMUP_TRIALS
--gantt-output-path GANTT_OUTPUT_PATH
                    Output file name/path for the Gantt chart. Does nothing unless `-g` or `--gantt` is also passed.
--wukong-config-file WUKONG_CONFIG_FILE
                    Path to the Wukong configuration file.
--faas-hostname FAAS_HOSTNAME
                    Hostname to pass to the FaaS client(s).
--faas-port FAAS_PORT
                    Port to pass to the FaaS client(s).
--task-metrics-output-file TASK_METRICS_OUTPUT_FILE
                    Output file path for task-level metrics. 
                    The file extension should be omitted, as this file path is used for both the pickle file and the CSV file.
--lambda-metrics-output-file LAMBDA_METRICS_OUTPUT_FILE
                    Output file path for serverless-function-level metrics. 
                    The file extension should be omitted, as this file path is used for both the pickle file and the CSV file.
--task-metrics- TASK_METRICS_
```

### The `run` Command

The `run` command should be specified __after__ specifying any top-level arguments. For example:

``` sh
python3 -m wukong.testing --num-trials 3 --num-invokers 8 run <experiment_name> <experiment_args>
```

There are a number of applications provided by default. These include the following:

```
tree_reduction (tr, tree-reduction)
                    Execute the "tree reduction" workload
linear (linear_dag, linear-dag)
                    Execute the "Linear DAG" workload
svd1 (svd-ts, svd-tall-and-skinny, svd-one)
                    Execute the "Tall-and-Skinny" SVD workload
svd2 (svd-compressed)
                    Execute the "Tall-and-Skinny" SVD workload
tsqr (tsqr, tall-and-skinny-qr-reduction)
                    Execute the "Tall-and-Skinny" QR reduction (TSQR) workload
generate-random-array (rand-array, gen-random-array, generate-random-arr, gen-rand-arr, gra)
                    Execute the "Generate Random Array" workload
gemm (matrix-multiplication, mat-mul, matmul)
                    Execute the "Tall-and-Skinny" GEMM workload
```

To view the arguments for a particular benchmark, specify the name of the benchmark when invoking the `run` command, and pass the `--help` flag.

For example:
``` sh
python3 -m wukong.testing run svd1 --help
```
```
usage: python3 -m wukong.testing run svd1 [-h] [-d1 DIMENSION1] [-d2 DIMENSION2] [-c1 CHUNK_DIMENSION1] [-c2 CHUNK_DIMENSION2]

Execute the "Tall-and-Skinny" SVD workload

options:
  -h, --help            show this help message and exit
  -d1 DIMENSION1, --dimension1 DIMENSION1
                        First dimension of the input array.
  -d2 DIMENSION2, --dimension2 DIMENSION2
                        Second dimension of the input array.
  -c1 CHUNK_DIMENSION1, --chunk-dimension1 CHUNK_DIMENSION1
                        First dimension of the chunk parameter. Default: 1,000
  -c2 CHUNK_DIMENSION2, --chunk-dimension2 CHUNK_DIMENSION2
                        Second dimension of the chunk parameter. Default: 100
```

## Defining New Experiments

To define a new experiment, create a new `.py` file for your experiment within the `wukong/testing/experiments` directory.

Any classes in the `wukong/testing/experiments` module MUST subclass the base `WukongExperiment` class, which is defined in the `wukong/testing/experiment.py` file.

After creating the new experiment class, add its import to the `wukong/testing/experiments/__init__.py` file as follows:
``` python
from .<NameOfYourPythonSourceFile> import <ClassName>
```

For example, if you defined a new Wukong experiment with a class name `MyCustomExperiment` in file `wukong/testing/experiments/my_custom_experiment.py`, then you would add the following line to the `wukong/testing/experiments/__init__.py` file:
``` python
from .my_custom_experiment import MyCustomExperiment
```
Notice that there is a dot (`.`) before the name of the `.py` file.

Adding such a line to the `__init__.py` file will enable the experiment to be automatically recognized and supported by the evaluation driver script.

### Methods to Implement/Override 
There are several methods that any subclass of `WukongExperiment` must implement/override. These are:
``` python
def __init__(self, args: argparse.Namespace):
    # Extract whatever arguments you added to the argument parser.
    self.arg1: int = getattr(args, "arg1", 0)
    self.arg2: str = getattr(args, "arg2", "")

    # Call the parent class' constructor, passing your experiment's 
    # name the aliases static variable, and the `args` parameter.
    #
    # Note: your experiment's name should match whatever name was passed to 
    # the argument parser in the call to `subparsers.add_parser` in
    # the `add_argument_parser` method.
    super().__init__("MyCustomExperiment", LinearDAGExperiment.aliases, args)

@staticmethod
def add_argument_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    # Create the subparser for your experiment. 
    # The name must be unique -- it cannot be the same as any other experiment's name.
    parser = subparsers.add_parser("MyCustomExperiment", 
        description = "Description of your experiment", 
        help = "Any helpful info about your experiment", 
        aliases = ExperimentClassName.aliases) 

    # Add any experiment-specific arguments here.
    parser.add_argument("-a1", "--arg1", type = int, default = 0, 
                        help = "This is my first experiment-specific argument.")
                        
    parser.add_argument("-a2", "--arg2", type = str, default = "", 
                        help = "This is my second experiment-specific argument.")

    # Make sure to return the subparser that you added/created at the end.
    return parser 

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
```

The most important of these methods are `execute` and `get_input_size_as_str`. These **must** be implemented in order for the experiment to be runnable. 

The `cleanup` and `prepare` methods may or may not be required, depending on the experiment that you are implementing. Many experiments may have no need for explicitly preparing or cleaning-up resources prior to execution. Note that the `prepare` and `cleanup` methods are each called **once**. `prepare` is called __before__ `execute` is called, and `cleanup` is called __after__ `execute` is called. They are __not__ called before/after each repeated trial of your experiment -- just once, at the beginning and end for `prepare` and `cleanup`, respectively. 

If you have tasks that should be executed before/after each repeated trial of your experiment, then these tasks should be performed at the very beginning and/or very end of your `execute` method. 

### Static Variables to Add

There is one static/class variable that you must add as well: `aliases`. `aliases` is a `list[str]` of other valid names for your experiment. This is simply for convenience.
``` python
from wukong.testing.experiment import WukongExperiment

class MyCustomExperiment(WukongExperiment):
    aliases: list[str] = ["mce", "custom-experiment", "custom-exp"] 
```

Your experiment can be invoked (via the `run` command of the `wukong.testing` module) using its "primary" name or any of its aliases. For example, the `svd1` experiment has several aliases, namely `"svd-ts"`, `"svd-tall-and-skinny"`, and `"svd-one"`. Any of the following commands would invoke the `svd1` experiment:
``` sh
python3 wukong.testing run svd1
python3 wukong.testing run svd-one
python3 wukong.testing run svd-ts
python3 wukong.testing run svd-tall-and-skinny
```

If you do not wish to provide any aliases for your experiment, simply define `aliases` to be an empty list.
``` python
from wukong.testing.experiment import WukongExperiment

class MyCustomExperiment(WukongExperiment):
    aliases: list[str] = [] 
```

**IMPORTANT**: Your experiment's name should match whatever name was passed to the argument parser in the call to `subparsers.add_parser` in the `add_argument_parser` method.