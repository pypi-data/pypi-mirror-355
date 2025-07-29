import pathlib

import click


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
	'--detailed',
	'-d',
	help='Display extra information about the project, i.e size. Takes longer to compute.',
	is_flag=True,
	default=False,
	show_default=True,
)
@click.option(
	'--force',
	'-f',
	help='Force recomputation of size and file count, ignoring cached values.',
	is_flag=True,
	default=False,
	show_default=True,
)
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
def project(
	directory: pathlib.Path | None, json: bool, detailed: bool, force: bool = False
) -> None:
	"""Display information about the current project.

	DIRECTORY is the path to the project directory,
	if not provided, the current working directory will be used.

	This command caches directory size and file count calculations to improve performance.
	By default, it will use cached values if available and if the directory hasn't been
	modified since the cache was created. Use --force to bypass the cache and recalculate
	all values.
	"""
	from damply.project import DirectoryAudit

	if directory is None:
		directory = pathlib.Path.cwd()
	directory = directory.resolve()
	audit = DirectoryAudit.from_path(directory)

	if detailed:
		audit.compute_details(show_progress=True, force=force)

	if json:
		print(audit.to_json())  # noqa
	else:
		from rich import print as rprint

		rprint(audit)
