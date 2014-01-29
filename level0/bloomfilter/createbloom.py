import pybloom
import sys

bloom = pybloom.BloomFilter(234937)

f = open("./test/data/words-6b898d7c48630be05b72b3ae07c5be6617f90d8e")
for line in f:
    word = line.rstrip()
    if word.lower() != word:
        continue
    bloom.add(word, skip_check=True)
bloom.tofile(open("bloom.dat", "w"))
