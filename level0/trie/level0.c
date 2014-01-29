#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alphabet.h"
#include "trie.h"

int main (int argc, char **argv) {
    char *path;
    if (argc > 1) {
        path = argv[1];
    } else {
        path = "/usr/share/dict/words";
    }

    FILE *f = fopen(path, "r");
    Trie *const trie = trie_build(f, alphabet_english, 30);
    fclose(f);

    char buf[BUFSIZ];
    while (fgets(buf, BUFSIZ, stdin)) {
        char *p = strtok(buf, " \n");
        while (p) {
            char *q = p;
            Trie *subtrie = trie;
            while (subtrie && *q) {
                char c = tolower(*q);
                if (subtrie->alphabet.index_for(c) == -1) {
                    subtrie = NULL;
                    break;
                }
                subtrie = *trie_child(*subtrie, c);
                q++;
            }

            if (subtrie && trie_has(*subtrie, "")) {
                printf("%s", p);
            } else {
                printf("<%s>", p);
            }
            if ((p = strtok(NULL, " \n"))) {
                printf(" ");
            }
        }
        if (!feof(stdin)) {
            printf("\n");
        }
    }


    return 0;
}
