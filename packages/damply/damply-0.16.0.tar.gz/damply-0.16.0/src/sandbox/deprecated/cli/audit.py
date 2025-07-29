from pathlib import Path

import click
from rich import print

from damply.audit import DirectoryAudit


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument(
	'path',
	type=click.Path(
		exists=True,
		path_type=Path,
		file_okay=True,
		dir_okay=True,
		readable=True,
	),
	default=Path().cwd(),
)
@click.option(
	'--json',
	is_flag=True,
	help='Output the audit results in JSON format.',
	default=False,
)
def audit(path: Path, json: bool) -> None:
	"""Audit the metadata of a valid DMP Directory."""

	try:
		audit = DirectoryAudit.from_path(path)
		if json:
			click.echo(audit.to_json())
		else:
			print(audit)
	except ValueError as e:
		print(e)
		return
