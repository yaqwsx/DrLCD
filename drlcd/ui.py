import click

from .acquire import measureLcd
from .image import visualize, compensate

@click.group()
def cli():
    pass

cli.add_command(measureLcd)
cli.add_command(visualize)
cli.add_command(compensate)

if __name__ == "__main__":
    cli()
