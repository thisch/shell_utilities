#!/usr/bin/env python2.7

import os
import subprocess
import time


USER = os.getlogin()


def qstat():
    q = subprocess.check_output(['qstat'])

    # filter relevant lines of qstat
    qsub_text = [ col.split() for col in q.splitlines() if USER in col ]

    # count running/queued jobs
    nrunning = []
    nqueue = []
    status_column = 4
    for d in qsub_text:
        if d[status_column] == "r":
            nrunning.append(d)
        if d[status_column] == "qw":
            nqueue.append(d)

    ntotal = len(qsub_text)
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

    return q


if __name__ == '__main__':
    while True:
        subprocess.call(['clear'])
        print qstat()
        time.sleep(5)
