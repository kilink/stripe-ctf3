#!/usr/bin/env python

import pybloom
import sys

filter = pybloom.BloomFilter.fromfile(open("bloom.dat"))

for line in sys.stdin:
    word = line.rstrip()
    for word in line.rstrip().split():
        if word.lower() in filter:
            print word,
        else:
            print "<" + word + ">",
    print
