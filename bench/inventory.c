/* Inventory only: public byte-oriented API; no algorithm modifications. */
#include "api.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main(void) {
    uint8_t pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
    uint8_t sig[CRYPTO_BYTES], msg[32] = {0};
    size_t len = 0, min = CRYPTO_BYTES, max = 0;
    unsigned long long total = 0;
    for (unsigned i = 0; i < 10000; ++i) {
        /* Fresh OS-random key every 100 messages; randomized public signer. */
        if (i % 100 == 0 && crypto_sign_keypair(pk, sk)) return 1;
        msg[0] = (uint8_t)i;
        msg[1] = (uint8_t)(i >> 8);
        if (crypto_sign_signature(sig, &len, msg, sizeof msg, NULL, 0, sk)) return 2;
        if (len > sizeof sig) return 3;
        if (crypto_sign_verify(sig, len, msg, sizeof msg, NULL, 0, pk)) return 4;
        if (len < min) min = len;
        if (len > max) max = len;
        total += len;
    }
    /* Confirm that verification rejects a modified message. */
    msg[0] ^= 1;
    if (!crypto_sign_verify(sig, len, msg, sizeof msg, NULL, 0, pk)) return 5;
    printf("%s,%d,%d,%d,%d,10000,%.6f,%zu,%zu\n", CRYPTO_ALGNAME,
           HAETAE_N, HAETAE_Q, CRYPTO_PUBLICKEYBYTES, CRYPTO_BYTES,
           (double)total / 10000, min, max);
    return 0;
}
