#!/bin/bash
# Remove whitespace and resize all input .jpg files.
# Usage: convert.sh FILE1.jpg FILE2.jpg ...

for i in "$@"; do
    BASE=$(basename $i .jpg)
    convert ${BASE}.jpg -fuzz 15% -transparent white -trim -resize 700x70! ${BASE}_resize.png
done
