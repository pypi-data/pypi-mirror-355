from ._core import __version__, device_info
import numpy as np


def cli():
    print(f"xlpd=={__version__}")
    device_info()


if __name__ == "__main__":
    cli()
