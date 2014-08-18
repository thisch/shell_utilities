#!/usr/bin/env python2.7

import argparse
import subprocess as sp
import sys
import os.path
import textwrap

# ----------------------------------------------------------------------
# Parsing command-line arguments
# ----------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--walltime", nargs="?", default=30, type=int,
                    help="Maximum job runtime (in minutes)" )
parser.add_argument("-N", "--name", default="SGE_job", type=str,
                    help="SGE job name" )
parser.add_argument("-n", "--nnodes", nargs="?", default=8, type=int,
                    help="Number of nodes on cluster" )
parser.add_argument("-e", "--executable", default="solve_xml_mumps",
                    type=str, help="Executable for job submission")
parser.add_argument("-i", "--input-xml", default="input.xml",
                    type=str, help="Input file for executable")
parser.add_argument("-a", "--array", nargs="+", type=str,
                    help="Submit list as array job to SGE cluster")
group = parser.add_mutually_exclusive_group()
group.add_argument("-c", "--cluster", action="store_true",
                    help="Submit job to SGE cluster")
group.add_argument("-l", "--local", action="store_true",
                    help="Run job locally")
args = parser.parse_args()

# ----------------------------------------------------------------------
# Print options
# ----------------------------------------------------------------------
print
print "Options:"
print
print "SGE job name:\t\t", args.name
print "Run on local node:\t", args.local
print "Run on SGE cluster:\t", args.cluster
print "Maximum job runtime:\t", args.walltime, "minutes"
print "Number of nodes:\t", args.nnodes
print "Executable file:\t", args.executable
print "Input xml-file:\t\t", args.input_xml
print "Array job directories:\t", args.array
print

# ----------------------------------------------------------------------
# Process arguments
# ----------------------------------------------------------------------
#try:
#    if not os.path.isfile(args.input_xml):
#        sys.exit()
#except:
#    print "Error: input xml %s not found" % (args.input_xml)


if args.local:
    with open("machines", "w") as f:
        f.write("localhost\n")

    sp.call("time mpirun -np 1 -machinefile machines %s -i %s" %
            (args.executable, args.input_xml), shell=True)

    
if args.cluster: 

    ARRAYJOB = ""
    if args.array:
        NJOBS = len(args.array)
        DIRS = "(" + " ".join(args.array) + ")"
    
        ARRAYJOB = """
            #$ -t 1-%s

            JOB_DIRS=%s
            INDEX=$((${SGE_TASK_ID} - 1))
            cd ${JOB_DIRS[${INDEX}]}            
        """ % (NJOBS, DIRS)
    
    OUTPUT = ""
    if not ARRAYJOB:
        OUTPUT = """
            #$ -o "tmp.out"
        """
        
    SGE_INPUT = """
            #!/bin/bash
            #$ -S /bin/bash
            #$ -cwd
            #$ -V
            #$ -N %s
            #$ -j y
            #$ -pe mpich %i
            #$ -l h_rt=00:%i:00   
            %s
            %s
        
            time mpirun -machinefile $TMPDIR/machines -np $NSLOTS %s -i %s
    """ % (args.name, args.nnodes, args.walltime, OUTPUT, ARRAYJOB,
           args.executable, args.input_xml)
    
    # Remove leading whitespace
    SGE_INPUT = textwrap.dedent(SGE_INPUT) 
    
    # Print SGE input file
    with open("SGE_INPUT.cfg", "w") as f:
        f.write(SGE_INPUT)

    # Open a pipe to the qsub command
    qsub = sp.Popen(["qsub"], stdin=sp.PIPE)    
    
    # Send SGE_input to qsub
    qsub.communicate(SGE_INPUT)
    
    print ""
    print "SGE settings:"
    print SGE_INPUT
