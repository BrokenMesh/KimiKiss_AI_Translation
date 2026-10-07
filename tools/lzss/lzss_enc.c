/*
 * LZSS encoder matching the engine's format (see tools/extract/lzss.py).
 * Haruhiko Okumura's 1989 LZSS.C binary-tree encoder with N=2048, F=34,
 * THRESHOLD=2, window filled with 0, and an 11-bit offset / 5-bit length
 * reference layout. Output starts with the u32 LE decompressed size.
 *
 * Usage: lzss_enc <in> <out>
 */
#include <stdio.h>
#include <stdlib.h>

#define N 2048
#define F 34
#define THRESHOLD 2
#define NIL N

static unsigned char text_buf[N + F - 1];
static int match_position, match_length;
static int lson[N + 1], rson[N + 257], dad[N + 1];

static void init_tree(void)
{
    int i;
    for (i = N + 1; i <= N + 256; i++) rson[i] = NIL;
    for (i = 0; i < N; i++) dad[i] = NIL;
}

static void insert_node(int r)
{
    int i, p, cmp = 1;
    unsigned char *key = &text_buf[r];

    p = N + 1 + key[0];
    rson[r] = lson[r] = NIL;
    match_length = 0;
    for (;;) {
        if (cmp >= 0) {
            if (rson[p] != NIL) p = rson[p];
            else { rson[p] = r; dad[r] = p; return; }
        } else {
            if (lson[p] != NIL) p = lson[p];
            else { lson[p] = r; dad[r] = p; return; }
        }
        for (i = 1; i < F; i++)
            if ((cmp = key[i] - text_buf[p + i]) != 0) break;
        if (i > match_length) {
            match_position = p;
            if ((match_length = i) >= F) break;
        }
    }
    dad[r] = dad[p]; lson[r] = lson[p]; rson[r] = rson[p];
    dad[lson[p]] = r; dad[rson[p]] = r;
    if (rson[dad[p]] == p) rson[dad[p]] = r;
    else lson[dad[p]] = r;
    dad[p] = NIL;
}

static void delete_node(int p)
{
    int q;

    if (dad[p] == NIL) return;
    if (rson[p] == NIL) q = lson[p];
    else if (lson[p] == NIL) q = rson[p];
    else {
        q = lson[p];
        if (rson[q] != NIL) {
            do { q = rson[q]; } while (rson[q] != NIL);
            rson[dad[q]] = lson[q]; dad[lson[q]] = dad[q];
            lson[q] = lson[p]; dad[lson[p]] = q;
        }
        rson[q] = rson[p]; dad[rson[p]] = q;
    }
    dad[q] = dad[p];
    if (rson[dad[p]] == p) rson[dad[p]] = q;
    else lson[dad[p]] = q;
    dad[p] = NIL;
}

int main(int argc, char **argv)
{
    FILE *in, *out;
    long size, pos = 0;
    unsigned char *src, code_buf[17], mask;
    int i, c, len, r, s, last_match_length, code_buf_ptr;

    if (argc != 3) { fprintf(stderr, "usage: %s <in> <out>\n", argv[0]); return 2; }
    if (!(in = fopen(argv[1], "rb"))) { perror(argv[1]); return 1; }
    fseek(in, 0, SEEK_END); size = ftell(in); fseek(in, 0, SEEK_SET);
    src = malloc(size ? size : 1);
    if (fread(src, 1, size, in) != (size_t)size) { perror("read"); return 1; }
    fclose(in);
    if (!(out = fopen(argv[2], "wb"))) { perror(argv[2]); return 1; }
    for (i = 0; i < 4; i++) putc((size >> (8 * i)) & 0xFF, out);

#define GETC() (pos < size ? src[pos++] : EOF)
    init_tree();
    code_buf[0] = 0;
    code_buf_ptr = mask = 1;
    s = 0; r = N - F;
    for (i = s; i < r; i++) text_buf[i] = 0;
    for (len = 0; len < F && (c = GETC()) != EOF; len++) text_buf[r + len] = c;
    if (len == 0) { fclose(out); return 0; }
    for (i = 1; i <= F; i++) insert_node(r - i);
    insert_node(r);
    do {
        if (match_length > len) match_length = len;
        if (match_length <= THRESHOLD) {
            match_length = 1;
            code_buf[0] |= mask;
            code_buf[code_buf_ptr++] = text_buf[r];
        } else {
            code_buf[code_buf_ptr++] = (unsigned char)match_position;
            code_buf[code_buf_ptr++] = (unsigned char)
                (((match_position >> 8) << 5) | (match_length - (THRESHOLD + 1)));
        }
        if ((mask <<= 1) == 0) {
            fwrite(code_buf, 1, code_buf_ptr, out);
            code_buf[0] = 0; code_buf_ptr = mask = 1;
        }
        last_match_length = match_length;
        for (i = 0; i < last_match_length && (c = GETC()) != EOF; i++) {
            delete_node(s);
            text_buf[s] = c;
            if (s < F - 1) text_buf[s + N] = c;
            s = (s + 1) & (N - 1); r = (r + 1) & (N - 1);
            insert_node(r);
        }
        while (i++ < last_match_length) {
            delete_node(s);
            s = (s + 1) & (N - 1); r = (r + 1) & (N - 1);
            if (--len) insert_node(r);
        }
    } while (len > 0);
    if (code_buf_ptr > 1) fwrite(code_buf, 1, code_buf_ptr, out);
    fclose(out);
    free(src);
    return 0;
}
