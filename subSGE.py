#!/usr/bin/env python2.7

import subprocess

import argparse
import textwrap


# ----------------------------------------------------------------------
# Parsing command-line arguments
# ----------------------------------------------------------------------
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
                    help="Submit list as job array to SGE cluster")

mode = parser.add_mutually_exclusive_group()
mode.add_argument("-c", "--cluster", action="store_true",
                  help="Submit job to SGE cluster")
mode.add_argument("-l", "--local", action="store_true",
                  help="Run job locally")

params = vars(parser.parse_args())


# ----------------------------------------------------------------------
# Print options
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# Process arguments
# ----------------------------------------------------------------------
if params.get("local"):
    with open("machines", "w") as f:
        f.write("localhost\n")

    cmd = ("time mpirun -np 1 -machinefile machines "
           "{executable} -i {input_xml}").format(**params)
    subprocess.call(cmd.split())


if params.get("cluster"):

    jobarray_settings = ""
    joblist = params.get("jobarray")
    if joblist:
        njobs = len(joblist)
        dirs = " ".join(joblist)

        jobarray_settings = """
            #$ -t 1-{0}

            JOB_DIRS=({1})
            INDEX=$((${SGE_TASK_ID} - 1))
            cd ${JOB_DIRS[${INDEX}]}
        """.format(njobs, dirs)

    tmp_file = ""
    if jobarray_settings is None:
        tmp_file = """
            #$ -o "tmp.out"
        """

    SGE_INPUT = """
            #!/bin/bash
            #$ -S /bin/bash
            #$ -cwd
            #$ -V
            #$ -N {name}
            #$ -j y
            #$ -pe mpich {nnodes}
            #$ -l h_rt=00:{walltime}:00
            {0}
            {1}

            time mpirun -machinefile $TMPDIR/machines -np $NSLOTS {executable} -i {input_xml}
    """.format(tmp_file, jobarray_settings, **params)

    # Remove leading whitespace
    SGE_INPUT = textwrap.dedent(SGE_INPUT)

    # Print SGE input file
    with open("SGE_INPUT.cfg", "w") as f:
        f.write(SGE_INPUT)
        print
        print "SGE settings:"
        print SGE_INPUT

    # Open a pipe to the qsub command
    qsub = subprocess.Popen(["qsub"], stdin=subprocess.PIPE)

    # Send SGE_input to qsub
    qsub.communicate(SGE_INPUT)
