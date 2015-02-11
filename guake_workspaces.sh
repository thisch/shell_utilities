#!/bin/bash
# Start guake and open 3 tabs (local bin, vsc bin, vsc)

guake & sleep 5

guake --rename-current-tab="1: local bin" --execute-command="ITP"
guake --new-tab=1 --rename-current-tab="2: VSC bin" --execute-command='ssh vsc -t "cd bin; /bin/bash --login"'
guake --new-tab=2 --rename-current-tab="3: VSC" --execute-command="ssh vsc"
