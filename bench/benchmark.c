/* Public byte API only. No algorithm or serialization changes. */
#include "api.h"
#include "dilithium/cpucycles.h"
#include "dilithium/speed_print.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint8_t pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
static uint8_t sig[CRYPTO_BYTES], msg[32];
static size_t siglen;

static void require(int ok, const char *what) {
    if (!ok) { fprintf(stderr, "FAILED: %s\n", what); exit(1); }
}

/* Read the two length offsets serialized by packing.c:pack_sig.
 * Do not scan backwards over zeros: a valid encoded component can end in zero. */
static size_t encoded_length(void) {
    const size_t pos = HAETAE_N / 8 + HAETAE_L * HAETAE_N;
    size_t len = pos + 2 + HAETAE_BASE_ENC_HB_Z1 + sig[pos]
                       + HAETAE_BASE_ENC_H + sig[pos + 1];
    require(siglen == CRYPTO_BYTES && len <= siglen, "encoded length");
    for (size_t j = len; j < siglen; ++j)
        require(sig[j] == 0, "zero padding");
    return len;
}

int main(int argc, char **argv) {
    require(argc == 4, "usage: benchmark timing_count correctness_count length_count");
    size_t nt = (size_t)strtoul(argv[1], NULL, 10);
    size_t nc = (size_t)strtoul(argv[2], NULL, 10);
    size_t nl = (size_t)strtoul(argv[3], NULL, 10);
    require(nt > 1 && nl > 0 && nc >= nl, "sample counts");
    unsigned long long total = 0;
    size_t max = 0;
    for (size_t i = 0; i < nc; ++i) {
        if (i % 100 == 0) require(!crypto_sign_keypair(pk, sk), "keypair");
        for (size_t j = 0; j < sizeof msg; ++j) msg[j] = (uint8_t)(i >> ((j % 4) * 8));
        require(!crypto_sign_signature(sig, &siglen, msg, sizeof msg, NULL, 0, sk), "sign");
        require(siglen == CRYPTO_BYTES, "fixed API size");
        require(!crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk), "verify");
        if (i < nl) {
            size_t len = encoded_length(); total += len;
            if (len > max) max = len;
        }
        msg[0] ^= 1;
        require(crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk) != 0, "modified message rejected");
        msg[0] ^= 1;
        sig[0] ^= 1;
        require(crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk) != 0, "modified signature rejected");
        sig[0] ^= 1;
    }
    printf("data,%s,%d,%d,%d,%d,%zu,%zu,%.6f,%zu\n", CRYPTO_ALGNAME,
           HAETAE_N, HAETAE_Q, CRYPTO_PUBLICKEYBYTES, CRYPTO_BYTES,
           nc, nl, (double)total / nl, max);

    uint64_t *t = calloc(nt + 1, sizeof *t);
    require(t != NULL, "timer allocation");
    /* Warm up each API outside measured samples. Sign and Verify always receive
     * serialized keys; all unpacking and OS randomness remain inside the API. */
    for (int op = 0; op < 3; ++op) {
        require(!crypto_sign_keypair(pk, sk), "warmup keypair");
        require(!crypto_sign_signature(sig, &siglen, msg, sizeof msg, NULL, 0, sk), "warmup sign");
        require(!crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk), "warmup verify");
        t[0] = 0;
        for (size_t i = 0; i < nt; ++i) {
            uint64_t start = cpucycles();
            int rc;
            if (op == 0) rc = crypto_sign_keypair(pk, sk);
            else if (op == 1) rc = crypto_sign_signature(sig, &siglen, msg, sizeof msg, NULL, 0, sk);
            else rc = crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk);
            uint64_t end = cpucycles();
            require(!rc, "timed API");
            /* Reconstruct consecutive timestamps from independent intervals for
             * unchanged print_results (which differences N+1 timestamps). */
            t[i + 1] = t[i] + end - start;
        }
        print_results(op == 0 ? "KeyGen" : op == 1 ? "Sign" : "Verify", t, nt + 1);
        if (op == 0) require(!crypto_sign_signature(sig, &siglen, msg, sizeof msg, NULL, 0, sk), "prepare signature");
        require(!crypto_sign_verify(sig, siglen, msg, sizeof msg, NULL, 0, pk), "post-timing verify");
    }
    free(t);
    return 0;
}
