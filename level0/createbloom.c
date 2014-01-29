#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libbloom/bitmap.h"
#include "libbloom/bloom.h"

int main (int argc, char **argv) {
    char buf[BUFSIZ];

    FILE *f = fopen("test/data/words-6b898d7c48630be05b72b3ae07c5be6617f90d8e", "r");
    bloom_bitmap bitmap;
    bloom_bloomfilter filter;
    bloom_filter_params params;
    params.bytes = 0;
    params.k_num = 0;
    params.capacity = 260000;
    params.fp_probability = 0.0001f;
    bf_params_for_capacity(&params);

    if(bitmap_from_filename("bloombitmap.dat", params.bytes, 1, PERSISTENT | NEW_BITMAP,
                &bitmap) == -1) {
        perror("bitmap_from_filename: ");
        exit(-1);
    }
    if (bf_from_bitmap(&bitmap, params.k_num, 1, &filter) == -1) {
        perror("bf_from_bitmap: ");
        exit(-1);
    }
    while (fgets(buf, BUFSIZ, f)) {
        int len = strlen(buf);
        buf[--len] = '\0';
        bf_add(&filter, buf);
    }
    fclose(f);
    bf_close(&filter);

    return 0;
}
