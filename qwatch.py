#!/usr/bin/env python2.7

import os
import subprocess
import time


USER = os.getlogin()

def qstat():
    q = subprocess.check_output(['qstat'])

    data_list = [ col.split() for col in q.splitlines() if USER in col ]
    nrunning = []
    nqueue = []
    for d in data_list:
        if d[4] == "r":
            nrunning.append(d)
        if d[4] == "qw":
            nqueue.append(d)

    ntotal = len(data_list)
    nrunning = len(nrunning)
    nqueue = len(nqueue)

    date = time.strftime("%a %b %d %H:%M:%S %Z %Y")
    print date

    print """
        SGE summary:
        ============
            Total number of submitted jobs: {1}
            Total number of running jobs:   {2}
            Total number of queued jobs:    {3}

    """.format(date, ntotal, nrunning, nqueue)

    return q


if __name__ == '__main__':
    while True:
        subprocess.call(['clear'])
        print qstat()
        time.sleep(5)
