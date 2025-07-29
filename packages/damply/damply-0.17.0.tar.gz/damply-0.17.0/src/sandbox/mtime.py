import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# ruff: noqa


@dataclass
class DirectoryModificationMetadata:
	directory: Path
	last_modification_time: Optional[int] = None
	last_modification_time_measured_at: Optional[datetime] = None

	def __post_init__(self):
		# Ensure the directory exists and is a directory
		self.validate_directory()

		# Initialize modification time and the measurement timestamp
		self.update_last_modification_time(initial=True)

	def validate_directory(self) -> None:
		"""Validate that the directory exists and is indeed a directory."""
		if not self.directory.exists():
			msg = f"Directory '{self.directory}' does not exist."
			raise FileNotFoundError(msg)
		if not self.directory.is_dir():
			msg = f"Path '{self.directory}' is not a directory."
			raise NotADirectoryError(msg)

	def get_last_modification_time(self) -> int:
		"""Recursively get the last modification time of the directory and its contents."""
		# if empty, modification time is just time of directory's actual modification and nothing to do with files
		last_mod_time = max(
			(f.stat().st_mtime for f in self.directory.rglob('*') if f.is_file()),
			default=self.directory.stat().st_mtime,
		)
		return int(last_mod_time)

	def update_last_modification_time(self, initial: bool = False) -> None:
		"""Update the stored last modification time and measurement timestamp."""
		self.last_modification_time = self.get_last_modification_time()
		self.last_modification_time_measured_at = datetime.now()
		if not initial:
			pass

	def update(self) -> None:
		"""Update the metadata if the directory has been modified since the last check."""
		if self.get_last_modification_time() != self.last_modification_time:
			self.update_last_modification_time(initial=True)

		self.get_file_count()
		self.get_total_size()
		self.has_subdirectories()

	def get_file_count(self) -> int:
		"""Get the total number of files in the directory."""
		return sum(1 for _ in self.directory.rglob('*') if _.is_file())

	def get_total_size(self) -> int:
		"""Calculate the total size of the directory."""
		return sum(f.stat().st_size for f in self.directory.rglob('*') if f.is_file())

	def has_subdirectories(self) -> bool:
		"""Check if the directory contains any subdirectories."""
		return any(f.is_dir() for f in self.directory.iterdir())

	def display(self) -> None:
		"""Display the metadata and check for modifications."""
		from rich.console import Console
		from rich.panel import Panel
		from rich.table import Table

		self.update()

		console = Console()
		table = Table(title=f'Directory: {self.directory.absolute()}')
		table.add_column('Property', justify='left', style='cyan', no_wrap=True)
		table.add_column('Value', justify='left', style='magenta')

		table.add_row(
			'Last modification time',
			str(datetime.fromtimestamp(self.last_modification_time)),
		)
		table.add_row(
			'Last modification time measured at',
			str(self.last_modification_time_measured_at),
		)
		table.add_row('File count', str(self.get_file_count()))
		table.add_row('Total size', str(self.get_total_size()))
		table.add_row('Has subdirectories', str(self.has_subdirectories()))

		panel = Panel(table, title='Directory Metadata', border_style='red')
		console.print(panel)


if __name__ == '__main__':
	# directory_path = Path("/path/to/your/directory")
	import tempfile
	import shutil
	import time
	from loguru import logger

	logger.info('Starting Directory Modification Metadata Test')

	directory_path = Path(tempfile.mkdtemp())

	logger.info(f'Created temporary directory: {directory_path}')
	metadata = DirectoryModificationMetadata(directory=directory_path)
	metadata.display()

	logger.info('Sleeping for 5 seconds to allow for initial modification time capture')
	time.sleep(5)
	# Create a file in the directory
	logger.info('Creating a new file in the directory')
	with open(os.path.join(directory_path, 'new_file.txt'), 'w') as f:
		f.write('New file content')

	metadata.display()

	logger.info('Sleeping for 2 seconds to allow for file creation')
	time.sleep(2)
	# Delete the file
	logger.info('Deleting the file created in the directory')
	os.remove(os.path.join(directory_path, 'new_file.txt'))
	metadata.display()

	logger.info('Removing the temporary directory')
	shutil.rmtree(directory_path)

# def test_complex_multiple_subdirectories():
#     """
#     This test will do the following:
#     1. Create a directory structure with multiple subdirectories
#     2. Create a file in each subdirectory
#     3. Record the last modification time of each subdirectory
#     4. Add a file to each subdirectory
#     5. Record the last modification time of each subdirectory. Ensure that the last modification time has changed.
#     6. Update one of the files in each subdirectory
#     7. Record the last modification time of each subdirectory. Ensure that the last modification time has changed.
#     """
#     import os
#     import shutil
#     import time
#     import tempfile

#     base_dir = tempfile.mkdtemp()
#     subdirs = [f'subdir_{i}' for i in range(5)]
#     files = [f'file_{i}.txt' for i in range(5)]

#     if os.path.exists(base_dir):
#         shutil.rmtree(base_dir)
#     os.mkdir(base_dir)

#     initial_times = {}
#     updated_times_after_add = {}
#     final_times_after_update = {}

#     try:
#         # Step 1: Create subdirectories
#         for subdir in subdirs:
#             os.mkdir(os.path.join(base_dir, subdir))

#         # Step 2: Create a file in each subdirectory
#         for subdir, file_name in zip(subdirs, files):
#             with open(os.path.join(base_dir, subdir, file_name), 'w') as f:
#                 f.write('Initial content')

#         # Step 3: Record the last modification time of each subdirectory and ensure it changed
#         dmm_list = [DirectoryModificationMetadata(directory=Path(os.path.join(base_dir, subdir))) for subdir in subdirs]
#         for dmm in dmm_list:
#             dmm.display()
#             assert dmm.get_last_modification_time() > 0, f"Modification time is not greater than 0 for {dmm.directory.absolute()}"
#         time.sleep(5)
#         print("\n\n")
#         # Step 4: Add a file to each subdirectory
#         for subdir in subdirs:
#             new_file_path = os.path.join(base_dir, subdir, 'new_file.txt')
#             with open(new_file_path, 'w') as f:
#                 f.write('New file content')

#         # Step 5: Record the last modification time of each subdirectory and ensure it changed
#         for dmm in dmm_list:
#             dmm.display()
#             assert dmm.get_last_modification_time() > 0, f"Modification time is not greater than 0 for {dmm.directory.absolute()}"

#         time.sleep(5)
#         print("\n\n")

#         # Check again
#         for dmm in dmm_list:
#             dmm.display()


#     finally:
#         # Cleanup
#         if os.path.exists(base_dir):
#             shutil.rmtree(base_dir)
