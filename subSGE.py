#!/usr/bin/env python2.7
"""Submit a job to the Sun Grid Engine (SGE).

usage: subSGE.py [-h] [-w [WALLTIME]] [-N NAME] [-n [NCORES]] [-e EXECUTABLE]
                 [-i INPUT_XML] [-a JOBARRAY [JOBARRAY ...]] [-d]

optional arguments:
    -h, --help            show this help message and exit
    -w [WALLTIME], --walltime [WALLTIME]
                            maximum job runtime (in minutes)
    -N NAME, --name NAME  SGE job name
    -n [NCORES], --ncores [NCORES]
                            number of cores on cluster
    -e EXECUTABLE, --executable EXECUTABLE
                            executable for job submission
    -i INPUT_XML, --input-xml INPUT_XML
                            input file for executable
    -a JOBARRAY [JOBARRAY ...], --jobarray JOBARRAY [JOBARRAY ...]
                            submit job array to cluster
    -d DRYRUN, --dryrun DRYRUN
                          write submit file and exit.
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
parser.add_argument("-N", "--name", default="SGE_job", type=str,
                    help="SGE job name")
parser.add_argument("-n", "--ncores", nargs="?", default=8, type=int,
                    help="number of cores on cluster")
parser.add_argument("-e", "--executable", default="solve_xml_mumps",
                    type=str, help="executable for job submission")
parser.add_argument("-i", "--input-xml", default="input.xml",
                    type=str, help="input file for executable")
parser.add_argument("-a", "--jobarray", nargs="+", type=str,
                    help="submit job array to cluster")
parser.add_argument("-d", "--dryrun", action="store_true",
                    help="write submit file and exit")

params = vars(parser.parse_args())

### print options
print """

    Options:

        SGE job name:           {name}
        Maximum job runtime:    {walltime} minutes
        Number of cores:        {ncores}
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
        #$ -t 1-{0}

        JOB_DIRS=({1})
        INDEX=$((${{SGE_TASK_ID}} - 1))
        cd ${{JOB_DIRS[${{INDEX}}]}}
    """.format(NJOBS, DIRS)
else:
    JOBARRAY_SETTINGS = ""

if not JOBARRAY_SETTINGS:
    TMP_FILE = """
        #$ -o "tmp.out"
    """
else:
    TMP_FILE = ""

SGE_OPTIONS = """
        #!/bin/bash
        #$ -S /bin/bash
        #$ -cwd
        #$ -V
        #$ -N {name}
        #$ -j y
        #$ -pe mpich {ncores}
        #$ -l h_rt=00:{walltime}:00
""".format(**params)

if params.get("executable") == "solve_xml_mumps":
    EXECUTABLE = """
        time mpirun -machinefile $TMPDIR/machines -np $NSLOTS {executable} -i {input_xml}
    """.format(**params)
else:
    EXECUTABLE = """
        export PYTHONUNBUFFERED=1
        time {executable}
    """.format(**params)

SGE_INPUT = SGE_OPTIONS + JOBARRAY_SETTINGS + TMP_FILE + EXECUTABLE

# remove leading whitespace
SGE_INPUT = textwrap.dedent(SGE_INPUT)

# print SGE input file
with open("SGE_INPUT.sh", "w") as f:
    f.write(SGE_INPUT)
    print
    print "SGE settings:"
    print SGE_INPUT

if params.get("dryrun"):
    sys.exit()

# open a pipe to the qsub command
qsub = subprocess.Popen(["qsub"], stdin=subprocess.PIPE)

# send SGE_input to qsub
qsub.communicate(SGE_INPUT)
