#!./bin/python
import bitstring
import collections
import hashlib
import io
import os
import os.path
import pygit2
import tempfile
import time

import multiprocessing



path = "level1"

repo = pygit2.Repository(path)
os.chdir(path)
difficulty = open("difficulty.txt").read().strip()

d = collections.OrderedDict()
f = io.BytesIO()
for line in open("LEDGER.txt", "r"):
    if ":" not in line:
        f.write(line)
        continue
    k,v = line.split(":")
    d[k] = int(v)

if "user-nsnkdc8h" in d:
    d["user-nsnkdc8h"] += 1
else:
    d["user-nsnkdc8h"] = 1

for k, v in d.items():
    f.write(k + ": " + bytes(v) + "\n")

with open("LEDGER.txt", "w") as ledger:
    ledger.write(f.getvalue())


timestamp = str(int(time.time())) + " +0000"
parent = repo.head.get_object().oid.hex
index = repo.index
index.read()
index.add("LEDGER.txt")
tree = index.write_tree()

template = """\
tree %(tree)s
parent %(parent)s
author *** <***@***> %(timestamp)s
committer *** <***@***> %(timestamp)s

Give me a damn Gitcoin!

nonce: """ % dict(parent=parent, timestamp=timestamp, tree=tree.hex)


def worker():
    while not found.is_set():
        block = queue.get()
        if block is None:
            return
        hash = hashlib.sha1("commit %d\0" % (len(template) + 8,) + template)
        for i in range(*block):
            h = hash.copy()
            nonce = bitstring.BitArray(uint=i, length=32).hex
            h.update(nonce)
            oid = h.hexdigest()
            if oid < difficulty:
                with lock:
                    if found.is_set():
                        return
                    found.set()
                commit = template + nonce
                fd, path = tempfile.mkstemp()
                with os.fdopen(fd, "w") as f:
                    f.write(commit)
                os.system("git hash-object -t commit -w %s" % path)
                os.system("git reset --hard %s" % oid)
                os.system("git push origin master")


max_workers = 8
i = 0
step = 2000000

lock = multiprocessing.Lock()
queue = multiprocessing.Queue(100)
found = multiprocessing.Event()

pool = multiprocessing.Pool(max_workers)
for i in range(max_workers):
    pool.apply_async(worker)

while not found.is_set():
    block = [i, i + step]
    queue.put(block)
    i += step
pool.close()
