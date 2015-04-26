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
  -i INPUT_XML, --input-xml INPUT_XML
                        input file for executable (default: input.xml)
  -a JOBARRAY [JOBARRAY ...], --jobarray JOBARRAY [JOBARRAY ...]
                        submit job array to queue (default: None)
  -d, --dryrun          write submit file and exit (default: False)
"""

import argparse
from argparse import ArgumentDefaultsHelpFormatter as help_formatter
import subprocess
import textwrap
import sys


### parse command-line arguments
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
parser.add_argument("-i", "--input-xml", default="input.xml",
                    type=str, help="input file for executable")
parser.add_argument("-a", "--jobarray", nargs="+", type=str,
                    help="submit job array to queue")
parser.add_argument("-d", "--dryrun", action="store_true",
                    help="write submit file and exit")
parser.add_argument("-p", "--tmp", action="store_true",
                    help="write output and error to tmp.out instead of slurm-SLURM-ID.out")

params = vars(parser.parse_args())

### print options
print """
    Options:

        Job name:               {name}
        Maximum job runtime:    {walltime} minutes
        Number of nodes:        {nnodes}
        Executable file:        {executable}
        Input xml file:         {input_xml}
        Job array directories:  {jobarray}

""".format(**params)

### process parameters
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
        #SBATCH --output="tmp.out"
        #SBATCH --error="tmp.out"
    """
else:
    TMP_FILE = ""

SLURM_OPTIONS = """
        #!/bin/bash

        #SBATCH --job-name={name}
        #SBATCH --time=00:{walltime}:00
        #SBATCH --nodes {nnodes}
        #SBATCH --ntasks-per-node={ntasks}
""".format(**params)
SLURM_OPTIONS = SLURM_OPTIONS[1:]

if params.get("executable") == "solve_xml_mumps":
    EXECUTABLE = """
        unset I_MPI_PIN_PROCESSOR_LIST
        time mpirun -np $SLURM_NTASKS {executable} -i {input_xml}
    """.format(**params)
else:
    EXECUTABLE = """
        export PYTHONUNBUFFERED=1
        time {executable}
    """.format(**params)

SLURM_INPUT = SLURM_OPTIONS + JOBARRAY_SETTINGS + TMP_FILE + EXECUTABLE

# remove leading whitespace
SLURM_INPUT = textwrap.dedent(SLURM_INPUT)

# print SLURM input file
with open("SLURM_INPUT.sh", "w") as f:
    f.write(SLURM_INPUT)
    print
    print "SLURM settings:"
    print SLURM_INPUT

if params.get("dryrun"):
    sys.exit()

# open a pipe to the sbatch command
sbatch = subprocess.Popen(["sbatch"], stdin=subprocess.PIPE)

# send SLURM_INPUT to sbatch
sbatch.communicate(SLURM_INPUT)
