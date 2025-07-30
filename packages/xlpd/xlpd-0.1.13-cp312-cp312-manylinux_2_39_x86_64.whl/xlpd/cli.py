from ._core import __version__, vector_add
import numpy as np


def cli():
    print(__version__)
    n = 5
    a = np.random.random(n)
    b = np.random.random(n)
    c = vector_add(a, b)
    print(f"{a} + {b} = {c}")


if __name__ == "__main__":
    cli()
