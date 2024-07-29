import click

import cwpl

@click.group()
def cli():
    pass

@cli.command()
def init_db():
    """initialize DB on first run"""
    print("Initialize DB!")
    cwpl.init_db()

@cli.command()
def run():
    """run CWPL report generator"""
    print("Run!")
    cwpl.show()


if __name__ == '__main__':
    cli()