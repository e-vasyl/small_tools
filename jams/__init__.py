import os, sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import click
from db import db
from ui import launch_server


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
    db.init_db()


@cli.command()
def run():
    """run Job Applications Memo UI [DEFAULT]"""

    print("Run!")
    launch_server()


# discourage use of this command for now
#
# if __name__ == "__main__":
#     cli()
