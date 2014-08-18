#!/usr/bin/env python2.7

import os
import subprocess
import time


USER = os.getlogin()
STATUS_COLUMN = 4


def qstat():
    """Return statistics of the SGE command 'qstat'."""

    qstat = subprocess.check_output(['qstat'])

    # filter relevant lines of qstat
    qstat_text = [ col.split() for col in qstat.splitlines() if USER in col ]

    # count running/queued jobs
    nrunning = []
    nqueue = []
    for d in qstat_text:
        if d[STATUS_COLUMN] == "r":
            nrunning.append(d)
        if d[STATUS_COLUMN] == "qw":
            nqueue.append(d)

    ntotal = len(qstat_text)
    nrunning = len(nrunning)
    nqueue = len(nqueue)

    date = time.strftime("%a %b %d %H:%M:%S %Z %Y")
    print date

    print """
        SGE summary:
        ============
            Total number of submitted jobs: {0}
            Total number of running jobs:   {1}
            Total number of queued jobs:    {2}

    """.format(ntotal, nrunning, nqueue)

    return qstat


def main(n=5):
    while True:
        subprocess.call(['clear'])
        print qstat()
        time.sleep(5)


if __name__ == '__main__':
    import argh
    argh.dispatch_command(main)
