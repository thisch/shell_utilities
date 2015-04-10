#!/bin/bash
# Remove whitespace and resize all input .jpg files.
# Usage: convert.sh FILE1.jpg FILE2.jpg ...

for i in "$@"; do
    DEST=$(basename $i .jpg)
    convert -fuzz 25% -transparent white -trim $i $i
    convert -resize 700x70! $i ${DEST}{,_resize}.jpg
done
