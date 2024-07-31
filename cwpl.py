import click

import cwpl


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    # execute default command
    if ctx.invoked_subcommand is None:
        run()


@cli.command()
def init_db():
    """initialize DB on first run"""

    print("Initialize DB!")
    cwpl.init_db()


@cli.command()
def run():
    """run CWPL report generator [DEFAULT]"""

    print("Run!")
    cwpl.show()


if __name__ == "__main__":
    cli()
