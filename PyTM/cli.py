from .__version__ import __version__
import click
from click import secho


def greet():
    secho("\n\033[1m✨ PyTM ✨\033[0m ", fg="green", nl=False)
    secho("CLI V-", nl=False)
    secho(__version__)
    secho("\033[1m----------------\033[0m")
    secho("\nTry 'pytm --help' for usage information.\n\n")


def print_version(ctx, param, value):
    if not value:
        return
    secho("\n\033[1m✨ PyTM ✨\033[0m ", fg="green", nl=False)
    secho("version ", nl=False)
    secho(__version__)
    ctx.exit()

@click.command()
@click.option('--version', '-v', '--v', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help="Shows version and exit")
def cli():
    """
    PyTM - CLI
    """
    greet()


if __name__ == "__main__":
    cli()
