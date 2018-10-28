"""
PyTM - CLI

"""
from .__version__ import __version__
import click
from click import secho


def greet():
    secho("\n\033[1mPyTM\033[0m ", fg="green", nl=False)
    secho("CLI V-", nl=False)
    secho(__version__)
    secho("\033[1m----------------\033[0m")
    secho("\nTry 'pytm --help' for usage information.\n\n")


@click.command()
@click.version_option(version=__version__)
def cli():
    greet()
if __name__ == "__main__":
    cli()

