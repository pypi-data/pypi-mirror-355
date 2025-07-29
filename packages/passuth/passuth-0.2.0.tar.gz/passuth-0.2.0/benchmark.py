from timeit import timeit

import passuth
from argon2 import PasswordHasher

text = "Test string for benchmarking the hash generation performance." * 10
hash_value = "$argon2id$v=19$m=19456,t=2,p=1$/+ZlHx+RMYUyOybKMXuVpQ$L8lQLQCheoLndOERC+17zTGDGpcPfEtOrZCetv++KaU"


def benchmark_generate_hash():
    return passuth.generate_hash(text)


def benchmark_verify_password():
    return passuth.verify_password(text, hash_value)


def benchmark_argon2_generate_hash():
    ph = PasswordHasher()
    return ph.hash(text)


def benchmark_argon2_verify_password():
    ph = PasswordHasher()
    return ph.verify(hash_value, text)


if __name__ == "__main__":
    print("Benchmarking passuth...")  # noqa: T201
    _ = timeit(benchmark_generate_hash, number=100)
    print("passuth generate:\t", timeit(benchmark_generate_hash, number=100))  # noqa: T201
    print("passuth verify:\t\t", timeit(benchmark_verify_password, number=100))  # noqa: T201
    print("argon2 generate:\t", timeit(benchmark_argon2_generate_hash, number=100))  # noqa: T201
    print("argon2 verify:\t\t", timeit(benchmark_argon2_verify_password, number=100))  # noqa: T201
