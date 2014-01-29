#!/bin/sh

# Add any build steps you need here

g++ -O4 -c -o murmurhash.o murmurhash/*.cpp
g++ -O4 -c -o spookyhash.o spookyhash/*.cpp
ar rvs murmurhash.a murmurhash.o
ar rvs spookyhash.a spookyhash.o

gcc -O4 --std=gnu99 level0bloom.c libbloom/*.c spookyhash.a murmurhash.a -lm -o level0

./level0 < long.txt
