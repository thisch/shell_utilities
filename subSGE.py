#!/usr/bin/env python2.7
"""Submit a job to the Sun Grid Engine (SGE).

usage: subSGE.py [-h] [-w [WALLTIME]] [-N NAME] [-n [NNODES]] [-e EXECUTABLE]
                 [-i INPUT_XML] [-j JOBARRAY [JOBARRAY ...]] [-c | -l]

optional arguments:
    -h, --help            show this help message and exit
    -w [WALLTIME], --walltime [WALLTIME]
                            Maximum job runtime (in minutes)
    -N NAME, --name NAME  SGE job name
    -n [NNODES], --nnodes [NNODES]
                            Number of nodes on cluster
    -e EXECUTABLE, --executable EXECUTABLE
                            Executable for job submission
    -i INPUT_XML, --input-xml INPUT_XML
                            Input file for executable
    -j JOBARRAY [JOBARRAY ...], --jobarray JOBARRAY [JOBARRAY ...]
                            Submit job array to cluster
    -c, --cluster         Submit job to SGE cluster
    -l, --local           Run job locally
"""

import argparse
import subprocess
import textwrap


### parse command-line arguments
parser = argparse.ArgumentParser()

parser.add_argument("-w", "--walltime", nargs="?", default=30, type=int,
                    help="Maximum job runtime (in minutes)")
parser.add_argument("-N", "--name", default="SGE_job", type=str,
                    help="SGE job name")
parser.add_argument("-n", "--nnodes", nargs="?", default=8, type=int,
                    help="Number of nodes on cluster")
parser.add_argument("-e", "--executable", default="solve_xml_mumps",
                    type=str, help="Executable for job submission")
parser.add_argument("-i", "--input-xml", default="input.xml",
                    type=str, help="Input file for executable")
parser.add_argument("-j", "--jobarray", nargs="+", type=str,
                    help="Submit job array to cluster")

mode = parser.add_mutually_exclusive_group()
mode.add_argument("-c", "--cluster", action="store_true",
                  help="Submit job to SGE cluster")
mode.add_argument("-l", "--local", action="store_true",
                  help="Run job locally")

params = vars(parser.parse_args())


### print options
print """

    Options:

        SGE job name:           {name}
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
            #$ -t 1-{0}

            JOB_DIRS=({1})
            INDEX=$((${SGE_TASK_ID} - 1))
            cd ${JOB_DIRS[${INDEX}]}
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
            #$ -pe mpich {nnodes}
            #$ -l h_rt=00:{walltime}:00
    """.format(**params)

    if params.get("executable") == "solve_xml_mumps":
        CMD = """
            time mpirun -machinefile $TMPDIR/machines -np $NSLOTS {executable} -i {input_xml}
        """.format(**params)
    else:
        CMD = """
            time {executable}
        """.format(**params)

    SGE_INPUT = SGE_OPTIONS + JOBARRAY_SETTINGS + TMP_FILE + CMD

    # remove leading whitespace
    SGE_INPUT = textwrap.dedent(SGE_INPUT)

    # print SGE input file
    with open("SGE_INPUT.sh", "w") as f:
        f.write(SGE_INPUT)
        print
        print "SGE settings:"
        print SGE_INPUT

    # open a pipe to the qsub command
    qsub = subprocess.Popen(["qsub"], stdin=subprocess.PIPE)

    # send SGE_input to qsub
    qsub.communicate(SGE_INPUT)
