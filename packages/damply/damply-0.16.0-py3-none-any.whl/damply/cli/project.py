import pathlib

import click


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument(
	'directory',
	type=click.Path(
		exists=True,
		file_okay=False,
		dir_okay=True,
		resolve_path=True,
		path_type=pathlib.Path,
	),
	default=None,
	required=False,
)
@click.option(
	'--json',
	'-j',
	is_flag=True,
	help='Output the audit information in JSON format.',
)
def project(directory: pathlib.Path | None, json: bool) -> None:
	"""Display information about the current project.

	DIRECTORY is the path to the project directory,
	if not provided, the current working directory will be used.
	"""
	from damply.project import DirectoryAudit

	if directory is None:
		directory = pathlib.Path.cwd()
	directory = directory.resolve()
	audit = DirectoryAudit.from_path(directory)

	if json:
		pass
	else:
		from rich import print as rprint

		rprint(audit)
