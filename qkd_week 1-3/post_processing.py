# =====================================================
# QKD Post-Processing Layer (Week 3)
# Includes: key sifting, error filtering, privacy amplification
# Not used in Week 4 (Key Management System phase)
# =====================================================


import random
import hashlib


def key_sifting(raw_key: str) -> str:
    """
    Simulate key sifting.
    In real QKD, mismatched measurement bases are discarded.
    Here, we randomly keep ~70% of the raw key bits.
    """

    sifted_bits = []

    for bit in raw_key:
        # Keep the bit with 70% probability
        if random.random() < 0.7:
            sifted_bits.append(bit)

    return "".join(sifted_bits)


def error_filtering(sifted_key: str) -> str:
    """
    Simulate error filtering.
    In real QKD, noisy bits are corrected or discarded.
    Here, we randomly drop bits to simulate error removal.
    """

    filtered_bits = []

    for bit in sifted_key:
        # Keep the bit with high probability (low noise)
        if random.random() < 0.95:
            filtered_bits.append(bit)

    return "".join(filtered_bits)


def privacy_amplification(filtered_key: str) -> str:
    """
    Simulate privacy amplification.
    In real QKD, this removes any partial information an eavesdropper may have.
    Here, we hash the key to produce a fixed-length final key.
    """

    # Hash the filtered key using SHA-256
    hash_object = hashlib.sha256(filtered_key.encode())

    # Return hexadecimal representation of the hash
    return hash_object.hexdigest()
