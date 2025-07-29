from __future__ import annotations

import subprocess
from pathlib import Path

from bytesize import ByteSize
from rich.progress import Progress, SpinnerColumn, TextColumn


def get_directory_size(directory: Path, show_progress: bool = True) -> ByteSize:
	if show_progress:
		with Progress(
			SpinnerColumn(),
			TextColumn('[progress.description]{task.description}'),
			transient=True,  # This makes the progress bar disappear after completion
		) as progress:
			task = progress.add_task(
				f'Calculating size of {str(directory.absolute())}...', total=None
			)
			result = subprocess.run(
				['du', '-s', '-B 1', str(directory)],
				capture_output=True,
				text=True,
				check=True,
			)
			progress.update(task, completed=True)
	else:
		result = subprocess.run(
			['du', '-s', '-B 1', str(directory)],
			capture_output=True,
			text=True,
			check=True,
		)

	size_ = ByteSize(int(result.stdout.split()[0]))
	return size_


def count_files(directory: Path, show_progress: bool = True) -> int:
	if show_progress:
		with Progress(
			SpinnerColumn(),
			TextColumn('[progress.description]{task.description}'),
			transient=True,
		) as progress:
			task = progress.add_task(
				f'Counting files in {str(directory.absolute())}...', total=None
			)
			count = sum(1 for p in directory.rglob('*') if p.is_file())
			progress.update(task, completed=True)
	else:
		count = sum(1 for p in directory.rglob('*') if p.is_file())

	return count


if __name__ == '__main__':
	import sys

	if len(sys.argv) != 2:
		sys.exit(1)
	directory_path = Path(sys.argv[1])
	if not directory_path.is_dir():
		sys.exit(1)
	size = get_directory_size(directory_path, show_progress=True)
