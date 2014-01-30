import binascii
import bitsets
import logging
import os
import os.path
import sys

log = logging.getLogger()
log.addHandler(logging.StreamHandler())


def trigrams(s, max=3):
    s = s.strip().lower()
    l = len(s)
    if l and l < max:
        return s.rjust(max)
    return [intern(str(s[i:i+max])) for i in range(l-max+1)]


class Index(object):

    _id = 0

    def __init__(self, shard_id=0, num_shards=3):
        self.shard_id = shard_id
        self.num_shards = num_shards
        self.doc_to_id = {}
        self.id_to_doc = {}
        self.linecache = {}
        self.trigram_to_docs = {}

    def clear(self):
        self.doc_to_id.clear()
        self.id_to_doc.clear()
        self.linecache.clear()
        self.trigram_to_docs.clear()
        self._id = 0

    def doc_id(self, doc):
        docid = self.doc_to_id.get(doc)
        if docid is None:
            self.doc_to_id[doc] = docid = self._id
            self.id_to_doc[self._id] = doc
            self._id += 1
        return docid

    def id_doc(self, docid):
        return self.id_to_doc.get(docid)

    def construct_bitset(self, path):
        paths = []
        path = os.path.abspath(path)
        for root, dirs, files in os.walk(path, followlinks=True):
            for filename in files:
                filepath = os.path.join(root, filename)
                if self.should_index(filepath):
                    p = os.path.relpath(os.path.join(root, filename), path)
                    paths.append(intern(str(p)))
        Documents = bitsets.bitset("Documents", tuple(paths))
        self.Documents = Documents
        return Documents

    def should_index(self, path):
        if not self.shard_id or self.num_shards < 2:
            return True
        h = binascii.crc32(path)
        return h % self.num_shards == (self.shard_id - 1)

    def index_path(self, path):
        Documents = self.construct_bitset(path)
        linecache = self.linecache
        index = self.trigram_to_docs
        for filename in Documents.supremum:
            docpath = os.path.join(path, filename)
            lines = open(docpath).readlines()
            linecache[filename] = lines
            doc = Documents([filename])
            for idx, line in enumerate(lines):
                for tgram in trigrams(line):
                    if tgram not in index:
                        index[tgram] = {idx: 0}
                    elif idx not in index[tgram]:
                        index[tgram][idx] = 0
                    index[tgram][idx] |= doc
            log.info("Node %d: indexed %s", self.shard_id or 0,
                     docpath)

    def search(self, query):
        trigram_to_docs = self.trigram_to_docs
        tlist = trigrams(query)
        if not tlist:
            return []
        Documents = self.Documents
        idx_to_doc = trigram_to_docs[tlist[0]].viewkeys()
        for trigram in tlist[1:]:
            idx_to_doc &= set(trigram_to_docs[trigram].viewkeys())
            if not idx_to_doc:
                return []

        idx = {k: v for k, v in trigram_to_docs[tlist[0]].items()
               if k in idx_to_doc}
        for trigram in tlist[1:]:
            for k in idx_to_doc:
                idx[k] &= trigram_to_docs[trigram][k]

        res = []
        linecache = self.linecache
        for linenum, docids in idx.items():
            for filename in Documents.fromint(docids):
                if query in linecache[filename][linenum]:
                    res.append(filename + ":" + str(linenum+1))
        return res
