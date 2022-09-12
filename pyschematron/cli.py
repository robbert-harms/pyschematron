__author__ = 'Robbert Harms'
__date__ = '2022-08-23'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

import signal
import sys
from pathlib import Path
from typing import Optional

import typer


app = typer.Typer(no_args_is_help=True)


if __name__ == "__main__":
    app = app()
