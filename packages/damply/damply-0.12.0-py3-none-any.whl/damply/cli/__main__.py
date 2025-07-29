import click
from damply.cli.project import project
from damply.cli.groups_table import groups_table
from damply import __version__


@click.group(context_settings={'help_option_names': ['-h', '--help']}, no_args_is_help=True)
@click.version_option(__version__, prog_name='damply')
def cli() -> None:
    """
    A tool to interact with systems implementing the
    Data Management Plan (DMP) standard.

    This tool is meant to allow sys-admins to easily query and audit the metadata of their
    projects.
    
    To enable logging, set the env variable `DAMPLY_LOG_LEVEL`.
    """
    pass

cli.add_command(project)
cli.add_command(groups_table)