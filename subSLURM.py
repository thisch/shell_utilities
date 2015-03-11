#!/usr/bin/env python2.7
"""Submit a job to the Slurm Workload Manager.

usage: subSLURM.py [-h] [-w [WALLTIME]] [-N NAME] [-n [NNODES]] [-e EXECUTABLE]
                 [-i INPUT_XML] [-a JOBARRAY [JOBARRAY ...]] [-d] [-c | -l]

optional arguments:
    -h, --help            show this help message and exit
    -w [WALLTIME], --walltime [WALLTIME]
                            maximum job runtime (in minutes)
    -N NAME, --name NAME  SLURM job name
    -n [NNODES], --nnodes [NNODES]
                            number of nodes on cluster
    -e EXECUTABLE, --executable EXECUTABLE
                            executable for job submission
    -i INPUT_XML, --input-xml INPUT_XML
                            input file for executable
    -a JOBARRAY [JOBARRAY ...], --jobarray JOBARRAY [JOBARRAY ...]
                            submit job array to cluster
    -d DRYRUN, --dryrun DRYRUN
                          write submit file and exit.
    -c, --cluster         submit job to cluster
    -l, --local           run job locally
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
parser.add_argument("-n", "--nnodes", nargs="?", default=16, type=int,
                    help="number of nodes to allocate")
parser.add_argument("-e", "--executable", default="solve_xml_mumps",
                    type=str, help="executable for job submission")
parser.add_argument("-i", "--input-xml", default="input.xml",
                    type=str, help="input file for executable")
parser.add_argument("-a", "--jobarray", nargs="+", type=str,
                    help="submit job array to cluster")
parser.add_argument("-d", "--dryrun", action="store_true",
                    help="write submit file and exit")

mode = parser.add_mutually_exclusive_group()
mode.add_argument("-c", "--cluster", action="store_true",
                  help="submit job to cluster")
mode.add_argument("-l", "--local", action="store_true",
                  help="run job locally")

params = vars(parser.parse_args())


### print options
print """

    Options:

        Job name:           {name}
        Run on local node:      {local}
        Run on cluster:         {cluster}
        Maximum job runtime:    {walltime} minutes
        Number of nodes:        {nnodes}
        Executable file:        {executable}
        Input xml file:         {input_xml}
        Job array directories:  {jobarray}

""".format(**params)


### process parameters
if params.get("local"):
    cmd = ("time {executable}").format(**params)
    subprocess.call(cmd.split())


if params.get("cluster"):
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

    if not JOBARRAY_SETTINGS:
        TMP_FILE = """
            #SBATCH --output="tmp.out"
            #SBATCH --error="tmp.err"
        """
    else:
        TMP_FILE = ""

    SLURM_OPTIONS = """
            #!/bin/bash
            #SBATCH --job-name={name}
            #SBATCH --time=00:{walltime}:00
            #SBATCH -N {nnodes}
            #SBATCH --ntasks-per-node=16
            #SBATCH --ntasks-per-core=1
    """.format(**params)

    if params.get("executable") == "solve_xml_mumps":
        EXECUTABLE = """
            unset I_MPI_PIN_PROCESSOR_LIST
            time mpirun -machinefile $TMPDIR/machines -np $NSLOTS {executable} -i {input_xml}
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

    # open a pipe to the qsub command
    qsub = subprocess.Popen(["sbatch"], stdin=subprocess.PIPE)

    # send SLURM_INPUT to qsub
    qsub.communicate(SLURM_INPUT)
