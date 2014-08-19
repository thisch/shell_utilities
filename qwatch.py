#!/usr/bin/env python2.7

import os
import subprocess
import time


# get $USER
USER = os.getlogin()
# column in qstat output to read status from
STATUS_COLUMN = 4


def qstat():
    """Process the SGE command 'qstat'."""

    # get qstat output
    qstat = subprocess.check_output(['qstat'])

    # filter relevant lines of qstat
    qstat_lines = [ line.split() for line in 
                     qstat.splitlines() if USER in line ]
    
    # get number of running/queued jobs
    njobs = dict()
    for status in "r", "qw":
        njobs[status] = len([ col for col in qstat_lines if 
                               status in col[STATUS_COLUMN] ])

    # take job arrays into account
    # TODO

    njobs["total"] = len(qstat_lines)

    # get current timestamp
    date = time.strftime("%a %b %d %H:%M:%S %Z %Y")
    print date

    # output
    print """
        SGE summary:
        ============
            Total number of submitted jobs: {total}
            Total number of running jobs:   {r}
            Total number of queued jobs:    {qw}

    """.format(**njobs)

    return qstat


def main(n=5):
    """Return usage statistics for the SGE command 'qstat'.
        
        Paramters:
        ----------
            n: int
                Update interval (seconds).
    """
    while True:
        subprocess.call(['clear'])
        print qstat()
        time.sleep(5)


if __name__ == '__main__':
    import argh
    argh.dispatch_command(main)
