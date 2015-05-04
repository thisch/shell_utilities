#!/usr/bin/env python
"""Submit a job to the SLURM Workload Manager.

usage: subSLURM.py [-h] [-w [WALLTIME]] [-N NAME] [-n [NNODES]] [-t [NTASKS]]
                   [-e EXECUTABLE] [-i INPUT_XML] [-a JOBARRAY [JOBARRAY ...]]
                   [-d]

optional arguments:
  -h, --help            show this help message and exit
  -w [WALLTIME], --walltime [WALLTIME]
                        maximum job runtime (in minutes) (default: 30)
  -N NAME, --name NAME  SLURM job name (default: SLURM_job)
  -n [NNODES], --nnodes [NNODES]
                        number of nodes to allocate (default: 1)
  -t [NTASKS], --ntasks [NTASKS]
                        number of tasks per node (default: 16)
  -e EXECUTABLE, --executable EXECUTABLE
                        executable for job submission (default:
                        solve_xml_mumps)
  --no-mpi              submit single-core job (default: False)
  -a JOBARRAY [JOBARRAY ...], --jobarray JOBARRAY [JOBARRAY ...]
                        submit job array to queue (default: None)
  -d, --dryrun          write submit file and exit (default: False)
  -p TMP, --tmp TMP     write output and error to TMP file instead to slurm-
                        SLURM-ID.out (default: None)
  -s, --silent          suppress output to stdout (default: False)
"""

import argparse
from argparse import ArgumentDefaultsHelpFormatter as help_formatter
import subprocess
import sys
import textwrap


# parse command-line arguments
parser = argparse.ArgumentParser(formatter_class=help_formatter)

parser.add_argument("-w", "--walltime", nargs="?", default=30, type=int,
                    help="maximum job runtime (in minutes)")
parser.add_argument("-N", "--name", default="SLURM_job", type=str,
                    help="SLURM job name")
parser.add_argument("-n", "--nnodes", nargs="?", default=1, type=int,
                    help="number of nodes to allocate")
parser.add_argument("-t", "--ntasks", nargs="?", default=16, type=int,
                    help="number of tasks per node")
parser.add_argument("-e", "--executable", default="solve_xml_mumps",
                    type=str, help="executable for job submission")
parser.add_argument("--no-mpi", action="store_true",
                    help="submit single-core job")
parser.add_argument("-a", "--jobarray", nargs="+", type=str,
                    help="submit job array to queue")
parser.add_argument("-d", "--dryrun", action="store_true",
                    help="write submit file and exit")
parser.add_argument("-p", "--tmp", type=str,
                    help=("write output and error to TMP file instead to "
                          "slurm-SLURM-ID.out"))
parser.add_argument("-s", "--silent", action="store_true",
                    help="suppress output to stdout")
parser.add_argument("-q", "--qos", type=str, default="normal_0064",
                    help="specify quality of service (QOS)")

params = vars(parser.parse_args())

# print options
if not params.get("silent"):
    print """
        Options:

            Job name:               {name}
            Maximum job runtime:    {walltime} minutes
            Number of nodes:        {nnodes}
            Executable file:        {executable}
            Job array directories:  {jobarray}
            Output files:           {tmp}
            Suppress stdout:        {silent}
            Quality of Service:     {qos}

    """.format(**params)

# process parameters
joblist = params.get("jobarray")
if joblist:
    NJOBS = len(joblist)
    DIRS = " ".join(joblist)

    JOBARRAY_SETTINGS = """
        #SBATCH --array 1-{0}

        JOB_DIRS=({1})
        INDEX=$((${{SLURM_ARRAY_TASK_ID}} - 1))
        cd ${{JOB_DIRS[${{INDEX}}]}}
    """.format(NJOBS, DIRS)
else:
    JOBARRAY_SETTINGS = ""

if params.get("tmp"):
    TMP_FILE = """
        #SBATCH --output={tmp}
        #SBATCH --error={tmp}
    """.format(**params)
else:
    TMP_FILE = ""

# assemble SLURM options
SLURM_OPTIONS = """
        #!/bin/bash

        #SBATCH --job-name={name}
        #SBATCH --time=00:{walltime}:00
        #SBATCH --nodes {nnodes}
        #SBATCH --ntasks-per-node={ntasks}
        #SBATCH --qos={qos}
""".format(**params)
SLURM_OPTIONS = SLURM_OPTIONS[1:]

if params.get("no_mpi"):
    MPI = ""
else:
    MPI = "mpirun -np $SLURM_NTASKS"

EXECUTABLE = """
        unset I_MPI_PIN_PROCESSOR_LIST
        time {MPI} {executable}
""".format(MPI=MPI, **params)

SLURM_INPUT = SLURM_OPTIONS + JOBARRAY_SETTINGS + TMP_FILE + EXECUTABLE

# remove leading whitespace
SLURM_INPUT = textwrap.dedent(SLURM_INPUT)

# print SLURM input file
with open("SLURM_INPUT.sh", "w") as f:
    f.write(SLURM_INPUT)
    if not params.get("silent"):
        print
        print "SLURM settings:"
        print SLURM_INPUT

if params.get("dryrun"):
    sys.exit()

# open a pipe to the sbatch command
sbatch = subprocess.Popen(["sbatch"], stdin=subprocess.PIPE)

# send SLURM_INPUT to sbatch
sbatch.communicate(SLURM_INPUT)
