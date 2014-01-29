#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "libbloom/bitmap.h"
#include "libbloom/bloom.h"

int main (int argc, char **argv) {

    bloom_bitmap bitmap;
    bloom_bloomfilter filter;
    bloom_filter_params params;
    params.capacity = 260000;
    params.fp_probability = 0.0001f;
    bf_params_for_capacity(&params);

    if (bitmap_from_filename("bloombitmap.dat", 623541, 0, SHARED, &bitmap) < 0) {
        perror("bitmap_from_filename: ");
        exit(-1);
    }
    if (bf_from_bitmap(&bitmap, params.k_num, 0, &filter) < 0) {
        perror("bf_from_bitmap: ");
        exit(-1);
    }

    char buf[BUFSIZ];
    while (fgets(buf, BUFSIZ, stdin)) {
        char *p = strtok(buf, " \n");
        while (p) {
            char *q = strdup(p);
            char *r = q;
            while (*q) {
                *q = tolower(*q);
                q++;
            }
            if (bf_contains(&filter, r)) {
                printf("%s", p);
            } else {
                printf("<%s>", p);
            }
            p = strtok(NULL, " \n");
            if (p) {
                printf(" ");
            }
            free(r);
        }
        if (!feof(stdin)) {
            printf("\n");
        }
    }


    return 0;
}
